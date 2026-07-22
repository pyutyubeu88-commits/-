#!/usr/bin/env python3
"""
네이버 블로그 자동 발행 — Playwright로 저장된 로그인 세션을 재사용해서
글쓰기 페이지를 조작한다.

⚠️ 본인 소유 블로그 전용. 클라이언트 계정에는 절대 사용하지 마라.
⚠️ 네이버 이용약관을 우회하는 방식이므로 계정 정지 리스크는 본인이 감수한다.
⚠️ 캡차/2단계인증/재로그인 화면이 보이면 즉시 중단한다 — 재시도하지 않는다.

사용법:
    python auto_publish.py drafts/20260721_153000.json --mode=draft
    python auto_publish.py drafts/20260721_153000.json --mode=publish

mode=draft (기본): 임시저장 버튼까지만 클릭한다. 안전한 테스트용.
mode=publish: 실제 발행 버튼까지 클릭한다. 시작 시 콘솔 확인(y/N)을 한 번 더 요구한다.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from random import uniform

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from rate_limiter import can_publish_today, record_publish
from telegram_alert import send_alert

# ── 경로 ──────────────────────────────────────────────────
SESSION_FILE = Path(__file__).parent / "session" / "naver_state.json"
LOG_DIR = Path(__file__).parent / "logs"
ATTEMPTS_LOG = LOG_DIR / "attempts.log"

# ── 네이버 블로그 셀렉터 ──────────────────────────────────
# TODO: 실제 셀렉터 확인 필요 — 아래 값들은 전부 추측/자리표시용이다.
# 반드시 실제 브라우저 개발자도구(F12)로 SmartEditor ONE의 정확한
# 셀렉터를 확인한 후 채워넣어야 한다. 네이버는 이 셀렉터를 자주 변경한다.
SELECTORS = {
    # 글쓰기 페이지 진입 후 제목 입력란
    # TODO: 실제 셀렉터 확인 필요
    "title_input": ".se-title-text .se-text-paragraph",
    # 본문 에디터가 iframe 안에 있는 경우 iframe 셀렉터
    # TODO: 실제 셀렉터 확인 필요
    "body_editor_iframe": "iframe.se-iframe",
    # 본문 에디터 내부 (iframe 안에서) 텍스트 입력 영역
    # TODO: 실제 셀렉터 확인 필요
    "body_editor": ".se-component-content .se-text-paragraph",
    # 임시저장 버튼
    # TODO: 실제 셀렉터 확인 필요
    "draft_button": "button.save_btn__bzc5B",
    # 발행 버튼 (임시저장과 별개로 "발행" 팝업을 여는 버튼)
    # TODO: 실제 셀렉터 확인 필요
    "publish_open_button": "button.publish_btn__M9KqF",
    # 발행 팝업 안의 최종 "발행" 확인 버튼
    # TODO: 실제 셀렉터 확인 필요
    "publish_confirm_button": "button.confirm_btn__WEaBq",
}

# TODO: 실제 URL 확인 필요 — 네이버 블로그 글쓰기 페이지 URL은
# blogId 파라미터가 필요할 수 있고 리다이렉트 방식이 바뀔 수 있다.
# 브라우저에서 직접 "글쓰기" 버튼을 눌러 실제 도달하는 URL을 확인하고 채워넣어라.
WRITE_PAGE_URL_TEMPLATE = "https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}"

# 이상 감지 키워드 — 페이지 텍스트에 이 단어들이 보이면 캡차/보안문자로 판단
ABORT_KEYWORDS = ["보안문자", "자동입력 방지", "비정상적인 접근", "캡차", "captcha"]

TIMEOUT_MS = 10_000


class AbortSignal(Exception):
    """이상 감지로 즉시 중단해야 할 때 발생시키는 예외."""


# ── 로깅 ──────────────────────────────────────────────────
def log_attempt(status: str, detail: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(ATTEMPTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {status}: {detail}\n")


def abort_and_alert(reason: str) -> None:
    """이상 감지 시 즉시 알림을 보내고 예외를 던져 스크립트를 중단시킨다. 재시도 없음."""
    message = f"[자동발행 중단] {reason}"
    send_alert(message)
    log_attempt("ABORTED", reason)
    raise AbortSignal(reason)


# ── 이상 감지 ─────────────────────────────────────────────
def check_for_danger(page: Page) -> None:
    """현재 URL과 페이지 텍스트를 검사해서 로그인 페이지 리다이렉트나
    캡차/보안문자 키워드가 있으면 abort_and_alert() 를 호출한다."""
    current_url = page.url

    if "nid.naver.com" in current_url:
        abort_and_alert(f"로그인 페이지로 리다이렉트됨 (세션 만료 의심): {current_url}")

    try:
        body_text = page.inner_text("body", timeout=3_000)
    except PlaywrightTimeoutError:
        body_text = ""

    for keyword in ABORT_KEYWORDS:
        if keyword.lower() in body_text.lower():
            abort_and_alert(f"이상 감지 키워드 '{keyword}' 페이지에서 발견됨: {current_url}")


# ── 사람처럼 타이핑 ───────────────────────────────────────
def human_type(page: Page, selector: str, text: str) -> None:
    """문자 단위로 30~120ms 랜덤 딜레이를 주면서 타이핑한다."""
    page.click(selector)
    for char in text:
        page.type(selector, char, delay=0)
        time.sleep(uniform(0.03, 0.12))


# ── 초안 로드 ─────────────────────────────────────────────
def load_draft(draft_path: Path) -> dict:
    if not draft_path.exists():
        raise FileNotFoundError(f"초안 파일을 찾을 수 없습니다: {draft_path}")
    return json.loads(draft_path.read_text(encoding="utf-8"))


# ── 메인 발행 로직 ────────────────────────────────────────
def publish_post(draft: dict, mode: str) -> None:
    if not SESSION_FILE.exists():
        raise FileNotFoundError(
            f"세션 파일이 없습니다: {SESSION_FILE}\n먼저 capture_session.py 를 실행하세요."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()

        # TODO: 실제 URL 확인 필요 — blog_id는 실제 본인 블로그 아이디로 교체해야 한다.
        # 아래는 자리표시용 값이다.
        blog_id = "TODO_NAVER_BLOG_ID"
        write_url = WRITE_PAGE_URL_TEMPLATE.format(blog_id=blog_id)

        print(f"글쓰기 페이지로 이동: {write_url}")
        page.goto(write_url, timeout=TIMEOUT_MS)
        check_for_danger(page)

        # 제목 입력
        try:
            page.wait_for_selector(SELECTORS["title_input"], timeout=TIMEOUT_MS)
        except PlaywrightTimeoutError:
            abort_and_alert(f"제목 입력란을 찾지 못함 (셀렉터 확인 필요): {SELECTORS['title_input']}")
        check_for_danger(page)
        human_type(page, SELECTORS["title_input"], draft["title"])

        # 본문 입력 — SmartEditor ONE은 보통 iframe 안에 에디터가 있다.
        try:
            frame = page.frame_locator(SELECTORS["body_editor_iframe"])
        except Exception:
            abort_and_alert(f"본문 에디터 iframe을 찾지 못함 (셀렉터 확인 필요): {SELECTORS['body_editor_iframe']}")

        for paragraph in draft["paragraphs"]:
            try:
                frame.locator(SELECTORS["body_editor"]).click(timeout=TIMEOUT_MS)
            except PlaywrightTimeoutError:
                abort_and_alert(f"본문 입력 영역을 찾지 못함 (셀렉터 확인 필요): {SELECTORS['body_editor']}")
            for char in paragraph:
                frame.locator(SELECTORS["body_editor"]).type(char, delay=0)
                time.sleep(uniform(0.03, 0.12))
            page.keyboard.press("Enter")

        check_for_danger(page)

        # 저장/발행
        if mode == "draft":
            try:
                page.click(SELECTORS["draft_button"], timeout=TIMEOUT_MS)
            except PlaywrightTimeoutError:
                abort_and_alert(f"임시저장 버튼을 찾지 못함 (셀렉터 확인 필요): {SELECTORS['draft_button']}")
            print("[완료] 임시저장까지 진행했습니다. (mode=draft — 실제 발행 아님)")
        else:  # publish
            try:
                page.click(SELECTORS["publish_open_button"], timeout=TIMEOUT_MS)
                page.click(SELECTORS["publish_confirm_button"], timeout=TIMEOUT_MS)
            except PlaywrightTimeoutError:
                abort_and_alert(
                    "발행 버튼을 찾지 못함 (셀렉터 확인 필요): "
                    f"{SELECTORS['publish_open_button']} / {SELECTORS['publish_confirm_button']}"
                )
            print("[완료] 발행까지 진행했습니다.")

        check_for_danger(page)
        browser.close()


def parse_args(argv: list[str]) -> tuple[Path, str]:
    if len(argv) < 2:
        print("사용법: python auto_publish.py drafts/<파일>.json --mode=draft|publish")
        sys.exit(1)

    draft_path = Path(argv[1])
    mode = "draft"
    for arg in argv[2:]:
        m = re.match(r"--mode=(draft|publish)", arg)
        if m:
            mode = m.group(1)

    return draft_path, mode


def main() -> int:
    draft_path, mode = parse_args(sys.argv)

    if mode == "publish":
        confirm = input("정말 자동 발행하시겠습니까? 실제로 네이버에 글이 올라갑니다. (y/N): ")
        if confirm.strip().lower() != "y":
            print("취소되었습니다.")
            return 0

    if not can_publish_today():
        send_alert(f"발행 거부: 하루 발행 제한 초과 ({draft_path.name})")
        log_attempt("REJECTED", f"rate limit exceeded, draft={draft_path.name}")
        return 1

    try:
        draft = load_draft(draft_path)
    except FileNotFoundError as e:
        print(f"[오류] {e}")
        log_attempt("FAILED", str(e))
        return 1

    try:
        publish_post(draft, mode)
    except AbortSignal:
        # abort_and_alert() 안에서 이미 알림/로그를 남겼으므로 여기서는 조용히 종료
        return 1
    except Exception as e:
        send_alert(f"발행 실패 ({draft_path.name}, mode={mode}): {e}")
        log_attempt("FAILED", f"draft={draft_path.name} mode={mode} error={e}")
        return 1

    if mode == "publish":
        record_publish()
    send_alert(f"발행 성공 ({draft_path.name}, mode={mode})")
    log_attempt("SUCCESS", f"draft={draft_path.name} mode={mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
