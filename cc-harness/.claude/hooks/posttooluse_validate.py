#!/usr/bin/env python3
"""
AI 하네스 — PostToolUse 검증 hook (클로드 코드)

파일 편집 후 실행되어:
  1. 변경 내용을 해시체인 감사 로그에 기록
  2. 편집된 파일에 대해 가벼운 검증 (구문 체크) 실행
  3. 문제 발견 시 Claude 에게 피드백 (additionalContext)

PostToolUse 는 이미 실행된 도구를 되돌릴 수 없으나, 피드백을 Claude 에 주입해
다음 행동을 교정하게 한다.
"""
import sys
import json
import os
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AUDIT_PATH = PROJECT_DIR / ".claude" / "harness-audit.jsonl"
GENESIS = "0" * 64


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_audit(stage: str, status: str, detail: str = ""):
    """해시체인 감사 로그에 항목 추가 (변조 방지)"""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev_hash, seq = GENESIS, 0
    if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
        try:
            for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    obj = json.loads(line)
                    prev_hash, seq = obj["hash"], obj["seq"]
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    entry = {
        "seq": seq + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "status": status,
        "detail": detail[:200],
        "prev_hash": prev_hash,
    }
    entry["hash"] = hashlib.sha256((prev_hash + _canonical(entry)).encode()).hexdigest()
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(_canonical(entry) + "\n")


def feedback(msg: str):
    """Claude 에게 피드백 주입 (PostToolUse additionalContext)"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"🛡 하네스 검증: {msg}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def quiet_ok():
    sys.exit(0)


def validate_python(file_path: Path) -> str | None:
    """Python 구문 검사 (실행 없이 컴파일만)"""
    try:
        import py_compile
        py_compile.compile(str(file_path), doraise=True)
        return None
    except py_compile.PyCompileError as e:
        return f"Python 구문 오류: {str(e)[:120]}"
    except Exception:
        return None


def validate_json(file_path: Path) -> str | None:
    try:
        json.loads(file_path.read_text(encoding="utf-8"))
        return None
    except json.JSONDecodeError as e:
        return f"JSON 형식 오류: {str(e)[:120]}"
    except Exception:
        return None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        quiet_ok()
        return

    tool = data.get("tool_name", "")
    tin = data.get("tool_input", {}) or {}
    fp = tin.get("file_path", "") or tin.get("path", "")

    # 감사 로그 기록 (모든 편집)
    if tool in ("Write", "Edit", "MultiEdit") and fp:
        append_audit("FILE_EDIT", "OK", f"{tool}: {fp}")

        path = Path(fp)
        if path.exists():
            problem = None
            if path.suffix == ".py":
                problem = validate_python(path)
            elif path.suffix == ".json":
                problem = validate_json(path)

            if problem:
                append_audit("VALIDATION", "FAILED", problem)
                feedback(f"{fp} — {problem}. 수정이 필요합니다.")

    quiet_ok()


if __name__ == "__main__":
    main()
