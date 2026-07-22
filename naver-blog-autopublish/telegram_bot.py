#!/usr/bin/env python3
"""
텔레그램 롱폴링 봇 — 모바일에서 명령을 보내면 이 컴퓨터가 대신
content_generate.py / auto_publish.py 를 실행해준다.

⚠️ 이 봇은 절대 Vercel 등 서버리스/클라우드에 배포하면 안 된다.
   매번 다른 IP에서 네이버 세션(session/naver_state.json)에 접근하면
   "다른 기기/위치에서의 비정상 접근"으로 FDS에 탐지되어 계정정지 위험이 커진다.
   반드시 session/naver_state.json 을 만든 바로 그 컴퓨터에서
   상시 실행되는 로컬 프로세스여야 한다 (long-polling 방식 — webhook/공개 URL 불필요).

사용법:
    python telegram_bot.py
    (Ctrl+C 로 종료)
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from rate_limiter import MAX_POSTS_PER_DAY, PUBLISH_LOG
from telegram_alert import send_message

load_dotenv()

# ── 경로/설정 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DRAFTS_DIR = BASE_DIR / "drafts"

TELEGRAM_API_BASE = "https://api.telegram.org"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("텔레그램 봇 토큰/채팅ID가 .env에 설정되어 있지 않습니다")
    sys.exit(1)

API_BASE = f"{TELEGRAM_API_BASE}/bot{BOT_TOKEN}"

CONTENT_GENERATE_TIMEOUT = 60  # LLM 호출
AUTO_PUBLISH_TIMEOUT = 120  # 브라우저 자동화

HELP_TEXT = (
    "사용법\n"
    "/포스팅 <주제> — 주제로 블로그 초안을 생성합니다\n"
    "/상태 — 오늘 발행 현황을 확인합니다\n"
)


# ── 텔레그램 API 헬퍼 ─────────────────────────────────────
# 메시지 전송은 telegram_alert.send_message() 를 그대로 재사용한다(중복 금지).
def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    try:
        requests.post(
            f"{API_BASE}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[콜백 응답 실패] {e}")


# ── 명령 처리 ──────────────────────────────────────────────
def handle_posting_command(topic: str) -> None:
    if not topic:
        send_message("사용법: /포스팅 <주제>")
        return

    send_message(f"생성 중... (주제: {topic})")

    result = subprocess.run(
        [sys.executable, "content_generate.py", topic],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=CONTENT_GENERATE_TIMEOUT,
    )

    match = re.search(r"\[완료\] 초안 저장: (.+)", result.stdout)
    if result.returncode != 0 or not match:
        detail = (result.stderr or result.stdout or "").strip()[-500:]
        send_message(f"초안 생성 실패\n{detail}")
        return

    draft_path = Path(match.group(1).strip())
    if not draft_path.is_absolute():
        draft_path = BASE_DIR / draft_path
    draft = json.loads(draft_path.read_text(encoding="utf-8"))

    title = draft.get("title", "")
    paragraphs = draft.get("paragraphs", [])
    preview_body = "\n\n".join(paragraphs[:3])
    if len(preview_body) > 300:
        preview_body = preview_body[:300] + "..."

    preview_text = f"{title}\n\n{preview_body}"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ 임시저장 진행", "callback_data": f"save:{draft_path.name}"},
                {"text": "🗑 폐기", "callback_data": f"discard:{draft_path.name}"},
            ]
        ]
    }
    send_message(preview_text, reply_markup=reply_markup)


def handle_status_command() -> None:
    from datetime import date

    today = date.today().isoformat()
    log = json.loads(PUBLISH_LOG.read_text(encoding="utf-8")) if PUBLISH_LOG.exists() else {}
    count_today = log.get(today, 0)
    send_message(f"오늘({today}) 발행: {count_today} / {MAX_POSTS_PER_DAY}")


def handle_text_message(text: str) -> None:
    text = text.strip()

    if text in ("/start", "/help"):
        send_message(HELP_TEXT)
    elif text.startswith("/포스팅"):
        topic = text[len("/포스팅"):].strip()
        handle_posting_command(topic)
    elif text == "/상태":
        handle_status_command()
    else:
        send_message("알 수 없는 명령입니다. /help 를 참고하세요.")


# ── 콜백 쿼리 처리 ─────────────────────────────────────────
def handle_callback_query(callback_query: dict) -> None:
    callback_query_id = callback_query["id"]
    data = callback_query.get("data", "")
    answer_callback_query(callback_query_id)

    if ":" not in data:
        return
    action, filename = data.split(":", 1)
    draft_path = DRAFTS_DIR / filename

    if action == "save":
        if not draft_path.exists():
            send_message(f"초안 파일을 찾을 수 없습니다: {filename}")
            return
        send_message(f"임시저장 진행 중... ({filename})")
        try:
            subprocess.run(
                [sys.executable, "auto_publish.py", str(draft_path)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=AUTO_PUBLISH_TIMEOUT,
            )
            # auto_publish.py 는 자체적으로 send_alert()로 성공/실패/중단을
            # 알리므로 봇은 결과를 중복으로 알리지 않는다.
        except subprocess.TimeoutExpired:
            send_message(f"임시저장 프로세스가 타임아웃되었습니다: {filename}")
        except Exception as e:
            send_message(f"임시저장 프로세스가 비정상 종료되었습니다: {filename}\n{e}")

    elif action == "discard":
        if draft_path.exists():
            draft_path.unlink()
            send_message(f"폐기했습니다: {filename}")
        else:
            send_message(f"초안 파일을 찾을 수 없습니다: {filename}")


# ── 롱폴링 루프 ────────────────────────────────────────────
def process_update(update: dict) -> None:
    if "callback_query" in update:
        callback_query = update["callback_query"]
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
        if chat_id != str(CHAT_ID):
            print(f"[무시] 알 수 없는 chat_id로부터의 콜백: {chat_id}")
            return
        handle_callback_query(callback_query)
        return

    message = update.get("message")
    if message is None:
        return

    chat_id = str(message.get("chat", {}).get("id", ""))
    if chat_id != str(CHAT_ID):
        print(f"[무시] 알 수 없는 chat_id로부터의 메시지: {chat_id}")
        return

    text = message.get("text", "")
    if text:
        handle_text_message(text)


def main() -> int:
    print("텔레그램 봇을 시작합니다 (Ctrl+C로 종료)...")
    offset = 0

    while True:
        try:
            resp = requests.get(
                f"{API_BASE}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            )
            resp.raise_for_status()
            updates = resp.json().get("result", [])
        except requests.RequestException as e:
            print(f"[getUpdates 실패] {e}")
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            try:
                process_update(update)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[업데이트 처리 실패] {e}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n봇을 종료합니다")
        sys.exit(0)
