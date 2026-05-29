#!/usr/bin/env python3
"""
AI 하네스 — PostToolUse 멀티패스 코드 리뷰 엔진

파일 편집 후 순차 실행:
  1. 해시체인 감사 로그 기록
  2. 언어별 린터 / 타입체커 (설치된 도구 자동 탐지)
  3. 관련 테스트 자동 발견 & 실행
  4. 반복 검토 횟수 추적 — MAX 초과 시 에스컬레이션

발견된 문제는 additionalContext 로 Claude 에 주입해 즉시 수정을 유도한다.
validate.py 의 감사 로그 기능을 통합했으므로 별도 실행 불필요.
"""
import sys
import json
import os
import hashlib
import shutil
import subprocess
import py_compile
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AUDIT_FILE  = PROJECT_DIR / ".claude" / "harness-audit.jsonl"
STATE_FILE  = PROJECT_DIR / ".claude" / "review-state.json"
GENESIS     = "0" * 64
MAX_ITER    = 5    # 동일 파일 연속 검토 최대 횟수
MAX_ISSUES  = 20   # 피드백에 포함할 최대 문제 수
TOOL_TIMEOUT = 30  # 외부 도구 실행 제한(초)


# ── 해시체인 감사 로그 ─────────────────────────────────────────
def _canon(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def append_audit(stage: str, status: str, detail: str = ""):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    prev, seq = GENESIS, 0
    if AUDIT_FILE.exists() and AUDIT_FILE.stat().st_size > 0:
        try:
            for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    o = json.loads(line)
                    prev, seq = o["hash"], o["seq"]
        except Exception:
            pass
    entry = {
        "seq":    seq + 1,
        "ts":     datetime.now(timezone.utc).isoformat(),
        "stage":  stage,
        "status": status,
        "detail": detail[:200],
        "prev":   prev,
    }
    entry["hash"] = hashlib.sha256((prev + _canon(entry)).encode()).hexdigest()
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(_canon(entry) + "\n")


# ── 세션 반복 추적 ─────────────────────────────────────────────
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            s = json.loads(STATE_FILE.read_text())
            start = datetime.fromisoformat(s.get("start", "2000-01-01T00:00:00+00:00"))
            if (datetime.now(timezone.utc) - start).total_seconds() < 86400:
                return s
        except Exception:
            pass
    return {"start": datetime.now(timezone.utc).isoformat(), "iters": {}}

def _save_state(s: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def increment_iter(fp: str) -> int:
    s = _load_state()
    s["iters"][fp] = s["iters"].get(fp, 0) + 1
    _save_state(s)
    return s["iters"][fp]


# ── 외부 도구 실행 ─────────────────────────────────────────────
def _run(*args) -> tuple:
    """(returncode | None, stdout+stderr). 도구 없으면 (None, '')."""
    if not shutil.which(args[0]):
        return (None, "")
    try:
        r = subprocess.run(
            list(args), capture_output=True, text=True,
            timeout=TOOL_TIMEOUT, cwd=PROJECT_DIR,
        )
        return (r.returncode, (r.stdout + r.stderr).strip())
    except subprocess.TimeoutExpired:
        return (1, f"[timeout {TOOL_TIMEOUT}s]")
    except Exception as e:
        return (1, str(e)[:100])


# ── 언어별 검사기 ──────────────────────────────────────────────
def _py_checks(fp: Path) -> list:
    issues = []

    # 1. 구문 (실행 없이 컴파일)
    try:
        py_compile.compile(str(fp), doraise=True)
    except py_compile.PyCompileError as e:
        return [f"❌ SYNTAX  {e}"]  # 구문 오류 → 이하 불필요

    # 2. flake8 — 스타일·논리 오류
    rc, out = _run("flake8", "--max-line-length=120", "--select=E,W,F,C90", str(fp))
    if rc and out:
        issues += [f"⚠ LINT    {l}" for l in out.splitlines()[:8]]

    # 3. mypy — 타입 오류
    rc, out = _run("mypy", "--ignore-missing-imports", "--no-error-summary", str(fp))
    if rc and out:
        issues += [f"⚠ TYPE    {l}" for l in out.splitlines() if "error:" in l][:6]

    # 4. bandit — 보안 취약점 (High/Medium 이상)
    rc, out = _run("bandit", "-q", "-ll", str(fp))
    if rc and out:
        issues += [f"🔴 SECURITY {l}" for l in out.splitlines() if l.startswith(">>")][:4]

    return issues

def _json_checks(fp: Path) -> list:
    try:
        json.loads(fp.read_text(encoding="utf-8"))
        return []
    except json.JSONDecodeError as e:
        return [f"❌ JSON    {e}"]

def _yaml_checks(fp: Path) -> list:
    rc, out = _run("yamllint", "-d", "relaxed", "--format", "parsable", str(fp))
    if rc and out:
        return [f"⚠ YAML    {l}" for l in out.splitlines()[:5]]
    return []

def _js_checks(fp: Path) -> list:
    rc, out = _run("node", "--check", str(fp))
    if rc and out:
        return [f"❌ SYNTAX  {out[:200]}"]
    return []

def _ts_checks(fp: Path) -> list:
    # tsc --noEmit: 프로젝트 tsconfig 기준, 해당 파일 오류만 필터
    rc, out = _run("npx", "--no", "tsc", "--noEmit")
    if rc and out:
        name = fp.name
        errs = [l for l in out.splitlines() if "error TS" in l and name in l]
        return [f"❌ TYPE    {l}" for l in errs[:6]]
    return []

def _sh_checks(fp: Path) -> list:
    rc, out = _run("shellcheck", "-S", "warning", str(fp))
    if rc and out:
        return [f"⚠ SHELL   {l}" for l in out.splitlines()[:6]]
    return []

def _dockerfile_checks(fp: Path) -> list:
    rc, out = _run("hadolint", "--no-fail", str(fp))
    if out:
        return [f"⚠ DOCKER  {l}" for l in out.splitlines()[:6]]
    return []

LANG_CHECKERS = {
    ".py":         _py_checks,
    ".json":       _json_checks,
    ".yaml":       _yaml_checks,
    ".yml":        _yaml_checks,
    ".js":         _js_checks,
    ".jsx":        _js_checks,
    ".ts":         _ts_checks,
    ".tsx":        _ts_checks,
    ".sh":         _sh_checks,
    "Dockerfile":  _dockerfile_checks,  # 파일명으로도 매칭
}

def get_checker(fp: Path):
    return LANG_CHECKERS.get(fp.suffix) or LANG_CHECKERS.get(fp.name)


# ── Claude API 수정 제안 ───────────────────────────────────────
def _ai_suggest_fix(fp: Path, issues: list) -> str:
    """Claude Haiku 로 구체적 수정 방법 제안. API 키 없으면 빈 문자열."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""
    try:
        import anthropic
        client  = anthropic.Anthropic(api_key=api_key)
        content = fp.read_text(encoding="utf-8", errors="replace")[:2500]
        issues_text = "\n".join(f"  {i+1}. {iss}" for i, iss in enumerate(issues[:10]))
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=(
                "당신은 코드 품질 전문가입니다. "
                "린터/테스트 오류를 분석해 개발자가 즉시 적용할 수 있는 "
                "구체적이고 간결한 수정 방법을 한국어로 알려주세요."
            ),
            messages=[{"role": "user", "content": (
                f"파일: `{fp.name}`\n\n"
                f"```{fp.suffix.lstrip('.')}\n{content}\n```\n\n"
                f"발견된 문제:\n{issues_text}\n\n"
                "각 문제에 대한 수정 방법을 번호 목록으로 간결하게 알려주세요. "
                "수정된 코드 스니펫을 포함하면 더 좋습니다."
            )}],
        )
        return resp.content[0].text.strip()
    except Exception:
        return ""


# ── 테스트 자동 발견 & 실행 ────────────────────────────────────
def _run_tests(fp: Path) -> list:
    stem = fp.stem.removeprefix("test_").removesuffix("_test")

    # Python: pytest
    if fp.suffix == ".py":
        candidates = [
            fp.parent / f"test_{stem}.py",
            fp.parent / f"{stem}_test.py",
            fp.parent / "tests" / f"test_{stem}.py",
            PROJECT_DIR / "tests" / f"test_{stem}.py",
        ]
        for test_fp in candidates:
            if test_fp.exists():
                rc, out = _run("python3", "-m", "pytest", str(test_fp),
                               "-x", "-q", "--tb=short")
                if rc is None:
                    break
                if rc != 0 and out:
                    lines = [l for l in out.splitlines() if l and "===" not in l]
                    return [f"🔴 TEST    {l}" for l in lines[:12]]
                return []  # 통과

    # JS/TS: jest
    if fp.suffix in (".js", ".jsx", ".ts", ".tsx"):
        rc, out = _run("npx", "--no", "jest", "--testPathPattern", stem,
                       "--no-coverage", "--passWithNoTests")
        if rc is not None and rc != 0 and out:
            lines = [l for l in out.splitlines()
                     if any(k in l for k in ("FAIL", "●", "Error:"))]
            return [f"🔴 TEST    {l}" for l in lines[:8]]

    return []


# ── 피드백 & 종료 ──────────────────────────────────────────────
def _feedback(msg: str):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }, ensure_ascii=False))
    sys.exit(0)

def _ok():
    sys.exit(0)


# ── 메인 ──────────────────────────────────────────────────────
def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _ok()
        return

    tool   = data.get("tool_name", "")
    tin    = data.get("tool_input", {}) or {}
    fp_str = tin.get("file_path", "") or tin.get("path", "")

    if tool not in ("Write", "Edit", "MultiEdit") or not fp_str:
        _ok()
        return

    fp = Path(fp_str)
    if not fp.exists():
        _ok()
        return

    # ── 감사 로그 ──
    append_audit("FILE_EDIT", "OK", f"{tool}: {fp_str}")

    # ── 반복 추적 ──
    n = increment_iter(fp_str)
    if n > MAX_ITER:
        _feedback(
            f"🚨 **하네스 에스컬레이션**: `{fp_str}` 가 {n}회 연속 검토됐으나 "
            f"문제가 지속됩니다. 자동 루프를 중단하고 **사용자에게 직접 확인을 요청**하세요."
        )
        return

    # ── 멀티패스 검토 ──
    checker    = get_checker(fp)
    lint_issues = checker(fp) if checker else []
    test_issues = _run_tests(fp)
    all_issues  = (lint_issues + test_issues)[:MAX_ISSUES]

    if all_issues:
        append_audit("REVIEW", "FAILED", f"{len(all_issues)} issues — {fp_str}")
        sep   = "━" * 52
        lines = [f"🔍 **코드 리뷰** — `{fp_str}` (검토 {n}/{MAX_ITER}회)", sep]
        lines += [f"  {i+1}. {iss}" for i, iss in enumerate(all_issues)]

        # Claude API 수정 제안 (API 키 있을 때만, 첫 3회까지만 호출)
        if n <= 3:
            suggestion = _ai_suggest_fix(fp, all_issues)
            if suggestion:
                lines.append(f"\n🤖 **AI 수정 제안**\n{suggestion}")

        if n >= MAX_ITER - 1:
            lines.append("\n⚠ 다음 검토가 마지막입니다. 해결 어려우면 사용자에게 에스컬레이션하세요.")
        else:
            lines.append("\n→ 위 문제를 수정하면 자동으로 재검토됩니다.")
        _feedback("\n".join(lines))
    else:
        append_audit("REVIEW", "PASSED", fp_str)
        _ok()


if __name__ == "__main__":
    main()
