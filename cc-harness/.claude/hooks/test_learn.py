#!/usr/bin/env python3
"""learn.py 단위 테스트 — 20개 케이스"""
import sys, json, os, re, tempfile, shutil
from pathlib import Path
from datetime import datetime, timezone

# learn.py 를 직접 import
sys.path.insert(0, str(Path(__file__).parent))
import learn as L

# ── 공통 헬퍼 (테스트 케이스 앞에 정의) ──────────────────────
def _compile_ok(pat: str) -> bool:
    try: re.compile(pat); return True
    except re.error: return False

def _match(pat: str, s: str) -> bool:
    try: return bool(re.search(pat, s.lower()))
    except re.error: return False

PASS = 0; FAIL = 0

def check(desc: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    mark = "✅" if condition else "❌"
    print(f"  {mark} {desc}")
    if not condition:
        FAIL += 1
        if detail:
            print(f"       {detail}")
    else:
        PASS += 1

# ── 픽스처 ────────────────────────────────────────────────────
def _event(decision, detail, tool="Bash", ts=None):
    return L.Event(
        ts or datetime.now(timezone.utc).isoformat(),
        decision, tool, detail
    )

def _make_events(deny_cmds: list, ask_cmds: list = None, bypass_cmds: list = None):
    events = []
    for cmd in (deny_cmds or []):
        events.append(_event("deny", cmd))
    for cmd in (ask_cmds or []):
        events.append(_event("ask", cmd))
    for cmd in (bypass_cmds or []):
        events.append(_event("allow_bypass", cmd))
    return events

print("=== learn.py 단위 테스트 ===\n")

# ── 1. 이벤트 파싱 ──
tmpdir = tempfile.mkdtemp()
efile  = Path(tmpdir) / ".claude" / "harness-events.jsonl"
efile.parent.mkdir(parents=True)

raw = [
    {"ts": "2026-05-28T10:00:00+00:00", "decision": "deny",         "tool": "Bash", "detail": "rm -rf /tmp"},
    {"ts": "2026-05-28T10:01:00+00:00", "decision": "ask",          "tool": "Bash", "detail": "git push origin main"},
    {"ts": "2026-05-28T10:02:00+00:00", "decision": "allow_bypass", "tool": "Bash", "detail": "rm -rf /tmp  # [harness-allow]"},
]
efile.write_text("\n".join(json.dumps(r) for r in raw))

L.EVENTS_FILE = efile
events = L.load_events()
check("이벤트 3개 파싱",         len(events) == 3)
check("deny 이벤트 1개",         sum(1 for e in events if e.decision == "deny") == 1)
check("ask 이벤트 1개",          sum(1 for e in events if e.decision == "ask") == 1)
check("allow_bypass 이벤트 1개", sum(1 for e in events if e.decision == "allow_bypass") == 1)

# ── 2. 빈 이벤트 파일 ──
efile2 = Path(tmpdir) / "empty-events.jsonl"
efile2.write_text("")
L.EVENTS_FILE = efile2
check("빈 파일 → 이벤트 0개", len(L.load_events()) == 0)
L.EVENTS_FILE = efile  # 복원

# ── 3. 패턴 시그니처 ──
check("rm -rf 시그니처",
      L.cmd_signature("rm -rf /important") == L.cmd_signature("rm -rf /other"),
      "같은 명령, 다른 경로 → 같은 시그니처여야 함")
check("kubectl 시그니처 (경로 인수 → 정규화)",
      L.cmd_signature("kubectl delete /namespace/foo") == L.cmd_signature("kubectl delete /namespace/bar"),
      "경로는 <PATH>로 치환되어 같은 시그니처가 되어야 함")

# ── 4. Analysis 기본 ──
# 경로 포함 명령어로 정규화 테스트 (foo/bar → <PATH>)
events10 = _make_events(
    deny_cmds=["kubectl delete /ns/foo"] * 8 + ["rm -rf /x"] * 2,
    ask_cmds=["git push origin main"] * 3,
    bypass_cmds=["kubectl delete /ns/bar"] * 4,   # bypass 4 / (deny 8 + bypass 4) = 33% > FP_RATIO(30%)
)
ana = L.Analysis(events10)
check("Analysis: deny 10개",    len(ana.denies)   == 10)
check("Analysis: ask 3개",      len(ana.asks)     == 3)
check("Analysis: bypass 4개",   len(ana.bypasses) == 4)

# ── 5. top_denied ──
top = ana.top_denied(3)
check("top_denied 1위: kubectl delete",
      "kubectl" in top[0][0] and "delete" in top[0][0],
      f"실제: {top[0]}")
check("top_denied 1위 빈도 8",  top[0][1] == 8)

# ── 6. 오탐 후보 탐지 (bypass/deny 같은 시그니처) ──
fp_cands = ana.false_positive_candidates()
check("오탐 후보 존재 (kubectl delete bypass 있음)", len(fp_cands) > 0,
      f"bypass={[L.cmd_signature(e.detail) for e in ana.bypasses]}, "
      f"deny={dict(ana.top_denied(3))}")
if fp_cands:
    sig, dc, bc, ratio = fp_cands[0]
    check("오탐 후보 bypass 비율 > 0", ratio > 0, f"ratio={ratio}")

# ── 7. new_pattern_candidates ──
policy_empty = {"protected_paths": [], "learned_rules": []}

# 빈도 충분 (>=3)한 이벤트 필요
events_rich = _make_events(
    deny_cmds=["kubectl delete pod foo"] * 12,
)
ana_rich = L.Analysis(events_rich)
candidates = ana_rich.new_pattern_candidates(policy_empty)
check("빈도 높은 패턴 → 후보에 포함",
      any("kubectl" in sig for sig, _, _ in candidates),
      f"candidates={candidates[:3]}")

# ── 8. 빈도 낮으면 후보 없음 ──
events_low = _make_events(deny_cmds=["kubectl delete pod foo"] * 2)
ana_low = L.Analysis(events_low)
cands_low = ana_low.new_pattern_candidates(policy_empty)
check("빈도 낮은 패턴 → 후보 없음 (MIN_FREQ=3)",
      len(cands_low) == 0, f"cands={cands_low}")

# ── 9. 폴백 regex 생성 ──
regex = L._fallback_regex("kubectl delete <PATH>", ["kubectl delete /ns/foo"])
check("폴백 regex 컴파일 가능", _compile_ok(regex), f"regex={regex}")
check("폴백 regex 예시 매칭",   _match(regex, "kubectl delete /ns/foo"), f"regex={regex}")
check("폴백 regex 정상 명령 미매칭", not _match(regex, "kubectl get pods"), f"regex={regex}")

# ── 10. apply_to_policy ──
policy_test = {"learned_rules": []}
rules = [{"pattern": r"\bkubectl\b.*\bdelete\b", "description": "test", "action": "deny"}]
updated, added = L.apply_to_policy(rules, policy_test)
check("apply_to_policy: 1개 추가",           added == 1)
check("apply_to_policy: learned_rules에 저장", len(updated["learned_rules"]) == 1)

# 중복 추가 방지
_, added2 = L.apply_to_policy(rules, updated)
check("apply_to_policy: 중복 추가 안 됨",   added2 == 0)

# ── 11. 정책 백업 ──
L.POLICY_FILE    = Path(tmpdir) / ".claude" / "harness-policy.json"
L.POLICY_HISTORY = Path(tmpdir) / ".claude" / "policy-history"
L.POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
L.POLICY_FILE.write_text('{"learned_rules":[]}')
backup = L.backup_policy()
check("정책 백업 파일 생성",     backup is not None and Path(backup).exists())

# ── 12. hourly_spike 기준선 ──
flat_events = _make_events(deny_cmds=["rm -rf /x"] * 3)  # 같은 시간대, 3개뿐
ana_flat = L.Analysis(flat_events)
check("spike 없음 (3개 이하)", len(ana_flat.hourly_spike()) == 0)

# ── 13. extract_raw ──
check("extract_raw — 구분자 ' — '",
      L.extract_raw("파괴적 명령 감지 — rm -rf /path") == "rm -rf /path")
check("extract_raw — 구분자 없음 (원본 반환)",
      L.extract_raw("kubectl delete pod foo") == "kubectl delete pod foo")

# ── 14. normalize_cmd ──
norm = L.normalize_cmd("rm -rf /home/user/project")
check("normalize_cmd: 경로 → <PATH>", "<PATH>" in norm, f"got: {norm}")

# ── 15. load_learn 기본값 ──
L.LEARN_FILE = Path(tmpdir) / ".claude" / "harness-learn-nonexistent.json"
cfg = L.load_learn()
check("load_learn 기본값 반환", "learned_patterns" in cfg)
check("load_learn min_freq_propose 기본값", cfg["min_freq_propose"] == L.MIN_FREQ_PROPOSE)

# ── 16. 이벤트 로그 없으면 empty Analysis ──
L.EVENTS_FILE = Path(tmpdir) / "no-events.jsonl"
empty_events = L.load_events()
ana_empty = L.Analysis(empty_events)
check("이벤트 없음 → Analysis 생성 가능", len(ana_empty.events) == 0)
check("이벤트 없음 → top_denied 빈 리스트", ana_empty.top_denied() == [])

# ── 17. cmd_signature 안정성 ──
s1 = L.cmd_signature("rm  -rf   /a/b/c")    # 공백 많음
s2 = L.cmd_signature("rm -rf /x/y/z")       # 다른 경로
check("같은 명령 다른 경로 → 같은 시그니처", s1 == s2, f"s1={s1} s2={s2}")

# ── 18. Analysis.false_positive_candidates 빈 bypass ──
no_bypass = _make_events(deny_cmds=["kubectl delete"] * 5)
ana_nb = L.Analysis(no_bypass)
check("bypass 없으면 오탐 후보 없음", len(ana_nb.false_positive_candidates()) == 0)

# ── 정리 ──────────────────────────────────────────────────────
shutil.rmtree(tmpdir, ignore_errors=True)
total = PASS + FAIL
print(f"\n결과: {PASS}/{total} 통과", "✅" if FAIL == 0 else f"— {FAIL}건 실패 ❌")
sys.exit(0 if FAIL == 0 else 1)
