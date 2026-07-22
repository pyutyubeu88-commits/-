#!/usr/bin/env python3
"""
네이버 로그인 세션 캡처 — 최초 1회(또는 세션 만료 시) 실행

Playwright로 헤드풀 크로미움을 열어 네이버 로그인 페이지로 이동한다.
아이디/비번/캡차/2단계인증은 전부 사람이 브라우저 창에서 직접 처리한다.
스크립트는 절대 로그인을 자동화하지 않는다 — 로그인 완료 후의
세션 쿠키(storage state)만 저장해서 이후 자동화 스크립트가 재사용하게 한다.

사용법:
    python capture_session.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# ── 경로 설정 ──────────────────────────────────────────────
SESSION_DIR = Path(__file__).parent / "session"
SESSION_FILE = SESSION_DIR / "naver_state.json"

NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
# 로그인 성공 시 보통 네이버 메인이나 마이페이지로 리다이렉트된다.
# 로그인 페이지(nid.naver.com/nidlogin)에 그대로 남아있으면 아직 로그인 전이라고 판단한다.


def is_logged_in(url: str) -> bool:
    """현재 URL이 로그인 페이지를 벗어났는지로 대략적인 로그인 완료 여부를 판단한다."""
    return "nidlogin" not in url


def main() -> int:
    SESSION_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # headless=False — 사람이 직접 로그인해야 하므로 반드시 헤드풀
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"네이버 로그인 페이지로 이동합니다: {NAVER_LOGIN_URL}")
        page.goto(NAVER_LOGIN_URL)

        print()
        print("=" * 60)
        print("브라우저 창에서 직접 로그인을 완료하세요.")
        print("아이디/비밀번호 입력, 캡차, 2단계 인증(OTP/SMS) 모두")
        print("사람이 수동으로 처리해야 합니다. 이 스크립트는 절대 대신 입력하지 않습니다.")
        print("로그인을 마친 후 이 터미널로 돌아와 Enter를 누르세요.")
        print("=" * 60)
        input()

        current_url = page.url
        if not is_logged_in(current_url):
            print(f"[오류] 아직 로그인 페이지에 머물러 있는 것 같습니다 (URL: {current_url})")
            print("로그인을 완료한 후 다시 시도하세요.")
            browser.close()
            return 1

        context.storage_state(path=str(SESSION_FILE))
        browser.close()

        print(f"[완료] 로그인 세션을 저장했습니다: {SESSION_FILE}")
        print("이제 auto_publish.py 에서 이 세션을 재사용할 수 있습니다.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
