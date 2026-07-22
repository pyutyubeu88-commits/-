#!/usr/bin/env python3
"""
하루 발행 개수 제한 — logs/publish_log.json 에 날짜별 발행 횟수를 기록한다.

MAX_POSTS_PER_DAY (.env, 기본 1)를 초과하면 can_publish_today() 가 False를 반환한다.
"""
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"
PUBLISH_LOG = LOG_DIR / "publish_log.json"
MAX_POSTS_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "1"))


def _load_log() -> dict:
    if not PUBLISH_LOG.exists():
        return {}
    return json.loads(PUBLISH_LOG.read_text(encoding="utf-8"))


def _save_log(log: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    PUBLISH_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


def can_publish_today() -> bool:
    """오늘 발행 횟수가 MAX_POSTS_PER_DAY 미만이면 True."""
    today = date.today().isoformat()
    log = _load_log()
    count_today = log.get(today, 0)

    if count_today >= MAX_POSTS_PER_DAY:
        print(f"[제한] 오늘({today}) 이미 {count_today}회 발행함. 하루 최대 {MAX_POSTS_PER_DAY}회 제한 초과.")
        return False
    return True


def record_publish() -> None:
    """발행 성공 시 오늘 날짜의 카운트를 1 증가시킨다."""
    today = date.today().isoformat()
    log = _load_log()
    log[today] = log.get(today, 0) + 1
    _save_log(log)
    print(f"[기록] 오늘({today}) 발행 횟수: {log[today]}")


if __name__ == "__main__":
    print(f"MAX_POSTS_PER_DAY={MAX_POSTS_PER_DAY}")
    print(f"오늘 발행 가능? {can_publish_today()}")
