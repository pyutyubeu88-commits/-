#!/usr/bin/env python3
"""
AI 하네스 — PreToolUse 보안 게이트 (클로드 코드 hook)

stdin 으로 도구 호출 JSON 을 받아 위험을 판정한다.
  - 차단: permissionDecision="deny" 출력
  - 허용: exit 0 (조용히 통과)
  - 검토: permissionDecision="ask" (사용자에게 확인 요청)

순수 Python — jq 등 외부 의존성 없음.
의미적 우회(rm -fr, find -delete 등)까지 잡도록 정규화 후 판정한다.
"""
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime, timezone

# ── 이벤트 로그 (자가 학습용) ─────────────────────────────────
_LOG_TOOL   = ""
_LOG_DETAIL = ""

def _log_event(decision: str):
    """deny/ask/allow_bypass 결정을 harness-events.jsonl 에 기록."""
    try:
        path = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "harness-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts":       datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "tool":     _LOG_TOOL,
            "detail":   _LOG_DETAIL[:300],
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 로깅 실패가 게이트를 멈추면 안 됨

# ── 설정 로드 (있으면 사용, 없으면 기본값) ───────────────────
def load_config():
    cfg_path = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "harness-policy.json"
    defaults = {
        "block_destructive": True,
        "block_secrets_access": True,
        "block_sudo": True,
        "protect_branches": ["main", "master", "production"],
        "protected_paths": [".env", ".env.*", "*.pem", "*.key", "id_rsa*",
                            "*.p12", "credentials*", ".aws/*", ".ssh/*"],
        "require_review_paths": ["*.prod.*", "config/production/*",
                                 "migrations/*", ".github/workflows/*"],
        "allow_token": "[harness-allow]",
    }
    if cfg_path.exists():
        try:
            user = json.loads(cfg_path.read_text(encoding="utf-8"))
            defaults.update(user)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


CFG = load_config()


def deny(reason: str):
    _log_event("deny")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"🛡 AI 하네스 차단: {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def ask(reason: str):
    _log_event("ask")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"👀 AI 하네스 검토 요청: {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def allow():
    sys.exit(0)


# ── 명령어 정규화 (우회 방지) ─────────────────────────────────
def normalize(cmd: str) -> str:
    """공백·플래그 순서 차이를 흡수해 의미적 우회를 잡는다."""
    c = cmd.lower()
    c = re.sub(r"\s+", " ", c)
    return c


# ── Bash 명령 위험 판정 ───────────────────────────────────────
def check_bash(command: str):
    norm = normalize(command)

    # 1) 파괴적 명령 — 플래그 순서·롱옵션 변형까지
    if CFG["block_destructive"]:
        destructive = [
            r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r|--recursive\s+--force|--force\s+--recursive)\b",
            r"\brm\s+-[a-z]*r[a-z]*\s+.*-[a-z]*f",       # rm -r ... -f
            r"\bfind\b.*-delete\b",
            r"\bdd\b.*of=/dev/(sd|nvme|hd)",
            r":\(\)\s*\{.*\|.*&\s*\}",                    # fork bomb
            r"\bmkfs\.",
            r">\s*/dev/(sd|nvme|hd)",
            r"\bshred\b",
            r"\bgit\s+.*reset\s+--hard.*&&.*push",
        ]
        for pat in destructive:
            if re.search(pat, norm):
                deny(f"파괴적 명령 감지 — {command[:60]}")

    # 2) sudo / 권한 상승
    if CFG["block_sudo"]:
        if re.search(r"\b(sudo|doas|su\s+-?\s*root|su\s+root)\b", norm):
            deny(f"권한 상승 명령 차단 — {command[:60]}")
        if re.search(r"\bchmod\s+(-[a-z]+\s+)?777\b", norm):
            deny(f"위험한 권한 변경(chmod 777) — {command[:60]}")

    # 3) 비밀 파일 접근 (cat/less/cp/scp 등)
    if CFG["block_secrets_access"]:
        secret_read = r"\b(cat|less|more|head|tail|cp|scp|rsync|curl|wget|tar|zip|base64)\b.*(\.env|\.pem|\bid_rsa\b|\.aws/|\.ssh/|credentials)"
        if re.search(secret_read, norm):
            deny(f"비밀 파일 접근/유출 시도 — {command[:60]}")
        # 환경변수 통째 유출
        if re.search(r"\b(env|printenv|set)\b.*\|.*\b(curl|wget|nc|netcat)\b", norm):
            deny("환경변수 외부 유출 시도")

    # 4) 보호 브랜치 직접 push — '/' 바로 앞에 오는 경우(feature/main 등)는 제외
    for branch in CFG["protect_branches"]:
        if re.search(rf"\bgit\s+push\b.*(?<!/){re.escape(branch)}\b", norm):
            ask(f"보호 브랜치 '{branch}' 직접 push — 확인 필요")
    if re.search(r"\bgit\s+push\b.*--force", norm):
        ask("force push 감지 — 확인 필요")

    # 5) 외부로의 파이프 실행 (curl | bash 류)
    if re.search(r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh|python|node)\b", norm):
        deny("원격 스크립트 즉시 실행(curl|bash) 차단")

    # 6) 자가 학습 엔진이 생성한 동적 규칙
    for rule in CFG.get("learned_rules", []):
        try:
            if re.search(rule.get("pattern", "(?!x)x"), norm):
                action = rule.get("action", "deny")
                desc   = rule.get("description", rule.get("pattern", ""))[:60]
                if action == "ask":
                    ask(f"학습 규칙 — {desc}")
                else:
                    deny(f"학습 규칙 차단 — {desc}")
        except re.error:
            pass  # 잘못된 패턴은 조용히 무시

    allow()


# ── 파일 쓰기/편집 위험 판정 ──────────────────────────────────
import fnmatch

def check_file_write(file_path: str, content: str = ""):
    if not file_path:
        allow()
    name = Path(file_path).name
    rel = file_path

    # 1) 보호 경로 — 차단
    for pat in CFG["protected_paths"]:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat):
            deny(f"보호 파일 수정 차단 — {file_path}")

    # 2) 검토 필요 경로
    for pat in CFG["require_review_paths"]:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat):
            ask(f"민감 경로 수정 — {file_path} (검토 필요)")

    # 3) 내용 내 하드코딩 시크릿
    if content:
        secret_pat = r'(?i)(password|passwd|api[_-]?key|secret|access[_-]?token|aws_secret)\s*[:=]\s*["\'`][^"\'`\s]{6,}'
        if re.search(secret_pat, content):
            deny(f"하드코딩 시크릿 감지 — {file_path}")
        # 위험 코드 패턴
        danger = [
            r"(?i)\beval\s*\(\s*(input|request|params)",
            r"(?i)\bexec\s*\(\s*(input|request|params)",
            r"(?i)subprocess\.\w+\([^)]*shell\s*=\s*True[^)]*\+",
            r"(?i)os\.system\s*\([^)]*\+",
        ]
        for pat in danger:
            if re.search(pat, content):
                ask(f"위험 코드 패턴 — {file_path} (검토 필요)")

    # 4) 자가 학습 엔진이 생성한 파일 경로 규칙
    norm_path = file_path.lower()
    for rule in CFG.get("learned_rules", []):
        if rule.get("scope") != "file":
            continue
        try:
            if re.search(rule.get("pattern", "(?!x)x"), norm_path):
                action = rule.get("action", "deny")
                desc   = rule.get("description", rule.get("pattern", ""))[:60]
                if action == "ask":
                    ask(f"학습 규칙 — {desc}")
                else:
                    deny(f"학습 규칙 차단 — {desc}")
        except re.error:
            pass

    allow()


# ── 메인 ──────────────────────────────────────────────────────
def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()  # 입력 파싱 실패 시 통과 (다른 게이트가 잡음)
        return

    tool = data.get("tool_name", "")
    tin  = data.get("tool_input", {}) or {}

    # 이벤트 로그용 컨텍스트 세팅
    global _LOG_TOOL, _LOG_DETAIL
    _LOG_TOOL   = tool
    _LOG_DETAIL = (tin.get("command", "") or tin.get("file_path", "") or tin.get("path", ""))[:300]

    # 면제 토큰이 명령어/내용에 포함된 경우 통과
    # Claude가 [harness-allow] 주석을 실행할 명령이나 내용에 포함하면 이 게이트를 우회
    if CFG.get("allow_token"):
        token = CFG["allow_token"]
        cmd_or_content = (
            tin.get("command", "") or
            tin.get("content", "") or
            tin.get("new_string", "") or ""
        )
        if token in cmd_or_content:
            _log_event("allow_bypass")
            allow()

    if tool == "Bash":
        check_bash(tin.get("command", ""))
    elif tool in ("Write", "Edit", "MultiEdit"):
        fp = tin.get("file_path", "") or tin.get("path", "")
        if tool == "MultiEdit":
            content = "\n".join(e.get("new_string", "") for e in tin.get("edits", []))
        else:
            content = tin.get("content", "") or tin.get("new_string", "") or ""
        check_file_write(fp, content)
    else:
        allow()


if __name__ == "__main__":
    main()
