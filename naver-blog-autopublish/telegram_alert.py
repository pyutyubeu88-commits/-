#!/usr/bin/env python3
"""
텔레그램 알림 — 발행 완료/실패/이상 감지 시 사용

.env 에 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 설정되어 있으면 텔레그램으로 전송하고,
없으면 콘솔에만 출력한다. 네트워크 오류가 나도 알림 전송 실패로 스크립트 전체가
죽으면 안 되므로 예외를 삼키고 콘솔에 에러만 남긴다.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_BASE = "https://api.telegram.org"


def send_alert(message: str) -> None:
    """텔레그램으로 알림을 보낸다. 설정이 없거나 전송 실패해도 예외를 던지지 않는다."""
    print(f"[알림] {message}")

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return  # 텔레그램 설정 없음 — 콘솔 출력으로 대체하고 조용히 넘어감

    try:
        resp = requests.post(
            f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"[텔레그램 전송 실패] status={resp.status_code} body={resp.text}")
    except requests.RequestException as e:
        print(f"[텔레그램 전송 실패] {e}")


if __name__ == "__main__":
    send_alert("텔레그램 알림 테스트입니다.")
