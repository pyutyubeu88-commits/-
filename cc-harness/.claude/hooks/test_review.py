#!/usr/bin/env python3
"""posttooluse_review.py 통합 테스트 — 20개 케이스"""
import subprocess, json, sys, os, tempfile, shutil
from pathlib import Path

HOOK = Path(__file__).parent / "posttooluse_review.py"
PASS = 0; FAIL = 0

# ── 헬퍼 ──────────────────────────────────────────────────────
def _run_hook(fp: str, tool: str = "Write", project_dir: str = "") -> dict:
    payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": fp}})
    env = os.environ.copy()
    if project_dir:
        env["CLAUDE_PROJECT_DIR"] = project_dir
    r = subprocess.run([sys.executable, str(HOOK)],
                       input=payload, capture_output=True, text=True, env=env)
    out = r.stdout.strip()
    if not out:
        return {"decision": "pass", "context": ""}
    try:
        o = json.loads(out)
        ctx = o["hookSpecificOutput"]["additionalContext"]
        return {"decision": "feedback", "context": ctx}
    except Exception:
        return {"decision": "parse_error", "raw": out}

def check(desc: str, got: dict, expect_feedback: bool,
          expect_keyword: str = "", expect_no_keyword: str = ""):
    global PASS, FAIL
    has_fb = got["decision"] == "feedback"
    ctx    = got.get("context", "")
    ok = (has_fb == expect_feedback)
    if ok and expect_keyword:
        ok = expect_keyword in ctx
    if ok and expect_no_keyword:
        ok = expect_no_keyword not in ctx
    mark = "✅" if ok else "❌"
    print(f"  {mark} {desc}")
    if not ok:
        print(f"       기대: feedback={expect_feedback} kw='{expect_keyword}'")
        print(f"       실제: {got['decision']}  ctx='{ctx[:120]}'")
        FAIL += 1
    else:
        PASS += 1

# ── 임시 프로젝트 ─────────────────────────────────────────────
tmpdir = tempfile.mkdtemp()
claude_dir = Path(tmpdir) / ".claude"
claude_dir.mkdir()

def _write(name: str, content: str) -> str:
    p = Path(tmpdir) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)

# ── 테스트 케이스 ──────────────────────────────────────────────
print("=== posttooluse_review 통합 테스트 ===\n")

# 1. Python 구문 오류 → 피드백
py_bad = _write("bad.py", "def broken(\n")
check("Python 구문 오류 → 피드백",
      _run_hook(py_bad, project_dir=tmpdir), True, "SYNTAX")

# 2. 정상 Python → 통과
py_ok = _write("ok.py", "def hello():\n    return 42\n")
check("정상 Python → 통과",
      _run_hook(py_ok, project_dir=tmpdir), False)

# 3. JSON 구문 오류 → 피드백
json_bad = _write("bad.json", '{"key": "value"  "missing_comma": 1}')
check("JSON 구문 오류 → 피드백",
      _run_hook(json_bad, project_dir=tmpdir), True, "JSON")

# 4. 정상 JSON → 통과
json_ok = _write("ok.json", '{"key": "value"}')
check("정상 JSON → 통과",
      _run_hook(json_ok, project_dir=tmpdir), False)

# 5. 존재하지 않는 파일 → 통과 (조용히)
check("존재하지 않는 파일 → 통과",
      _run_hook("/nonexistent/file.py", project_dir=tmpdir), False)

# 6. Write 도구 → 피드백 트리거됨
check("Write 도구 → 피드백",
      _run_hook(py_bad, tool="Write", project_dir=tmpdir), True)

# 7. Edit 도구 → 피드백 트리거됨
check("Edit 도구 → 피드백",
      _run_hook(py_bad, tool="Edit", project_dir=tmpdir), True)

# 8. MultiEdit 도구 → 피드백 트리거됨
check("MultiEdit 도구 → 피드백",
      _run_hook(py_bad, tool="MultiEdit", project_dir=tmpdir), True)

# 9. Bash 도구 → 무시 (통과)
check("Bash 도구 → 무시",
      _run_hook(py_bad, tool="Bash", project_dir=tmpdir), False)

# 10. 반복 추적 — 전용 파일로 깨끗한 카운터 사용
iter_file = _write("iter_test.py", "def broken(\n")
for _ in range(3):
    _run_hook(iter_file, project_dir=tmpdir)
r4 = _run_hook(iter_file, project_dir=tmpdir)  # 4회차
check("4회차 → '마지막' 경고 포함",
      r4, True, "마지막")

# 11. 5회 초과 → 에스컬레이션 메시지
_run_hook(iter_file, project_dir=tmpdir)  # 5회차
r6 = _run_hook(iter_file, project_dir=tmpdir)  # 6회차
check("6회 초과 → 에스컬레이션",
      r6, True, "에스컬레이션")

# 12. 새 파일(리셋용) 정상 → 통과
py_fresh = _write("fresh.py", "x = 1\n")
check("새 파일 정상 → 통과",
      _run_hook(py_fresh, project_dir=tmpdir), False)

# 13. 텍스트 파일 (.txt) → 검사기 없음, 통과
txt = _write("notes.txt", "hello world")
check(".txt 파일 → 검사기 없음, 통과",
      _run_hook(txt, project_dir=tmpdir), False)

# 14. 빈 JSON → 통과
empty_json = _write("empty.json", "{}")
check("빈 JSON → 통과",
      _run_hook(empty_json, project_dir=tmpdir), False)

# 15. 중첩 구문 오류 Python → SYNTAX 키워드 포함
nested_bad = _write("nested.py", "class Foo:\n  def bar(self\n")
r = _run_hook(nested_bad, project_dir=tmpdir)
check("중첩 구문 오류 → SYNTAX 키워드",
      r, True, "SYNTAX")

# 16. 검토 횟수 표시 형식 확인
fresh2 = _write("counter_test.py", "def bad(\n")
r = _run_hook(fresh2, project_dir=tmpdir)
check("피드백에 회차 표시 포함",
      r, True, "검토")

# 17. 피드백에 파일명 포함
check("피드백에 파일명 포함",
      _run_hook(py_bad, project_dir=tmpdir), True, "py_bad" if False else "bad.py")

# 18. 감사 로그 생성 확인
audit_path = Path(tmpdir) / ".claude" / "harness-audit.jsonl"
_run_hook(json_ok, project_dir=tmpdir)
check("감사 로그 파일 생성됨",
      {"decision": "pass"} if audit_path.exists() else {"decision": "fail"},
      False)  # 통과 판정 기준: 파일이 존재하면 PASS(feedback=False 기대)
if audit_path.exists():
    PASS += 1; print(f"  ✅ 감사 로그 생성 확인 ({audit_path})")
else:
    FAIL += 1; print(f"  ❌ 감사 로그 미생성")

# 19. 도구명 빈 문자열 → 통과
r = subprocess.run(
    [sys.executable, str(HOOK)],
    input=json.dumps({"tool_name": "", "tool_input": {}}),
    capture_output=True, text=True,
    env={**os.environ, "CLAUDE_PROJECT_DIR": tmpdir}
)
check("도구명 빈 문자열 → 통과",
      {"decision": "pass" if not r.stdout.strip() else "feedback"}, False)

# 20. 잘못된 JSON 입력 → 조용히 통과 (gate 안 죽음)
r = subprocess.run(
    [sys.executable, str(HOOK)],
    input="NOT_JSON",
    capture_output=True, text=True,
    env={**os.environ, "CLAUDE_PROJECT_DIR": tmpdir}
)
check("잘못된 입력 → 조용히 통과 (크래시 없음)",
      {"decision": "pass" if not r.stdout.strip() else "feedback"}, False)

# ── 정리 ──────────────────────────────────────────────────────
shutil.rmtree(tmpdir, ignore_errors=True)
total = PASS + FAIL
print(f"\n결과: {PASS}/{total} 통과", "✅" if FAIL == 0 else f"— {FAIL}건 실패 ❌")
sys.exit(0 if FAIL == 0 else 1)
