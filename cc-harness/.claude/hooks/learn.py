#!/usr/bin/env python3
"""
AI 하네스 — 자가 학습 엔진

harness-events.jsonl 을 분석해 보안 정책을 자동으로 진화시킨다.

사용법:
  python3 .claude/hooks/learn.py              # 요약 분석
  python3 .claude/hooks/learn.py --report     # 전체 리포트 (오탐 후보 + 신규 패턴 제안)
  python3 .claude/hooks/learn.py --apply      # 고신뢰 패턴 자동 적용
  python3 .claude/hooks/learn.py --reset      # 이벤트 로그 초기화

학습 흐름:
  deny/ask 이벤트 수집 → 패턴 추출 → 빈도 분석 → 신뢰도 계산
  → 신규 패턴 제안 → [고신뢰] 자동 적용 / [중간] 리포트 출력
  → harness-policy.json 업데이트 (버전 히스토리 유지)
"""
import sys
import json
import re
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from typing import NamedTuple

PROJECT_DIR    = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
EVENTS_FILE    = PROJECT_DIR / ".claude" / "harness-events.jsonl"
POLICY_FILE    = PROJECT_DIR / ".claude" / "harness-policy.json"
LEARN_FILE     = PROJECT_DIR / ".claude" / "harness-learn.json"
POLICY_HISTORY = PROJECT_DIR / ".claude" / "policy-history"

# ── 임계값 ────────────────────────────────────────────────────
MIN_FREQ_PROPOSE = 3       # 제안 최소 빈도
MIN_FREQ_APPLY   = 10      # 자동 적용 최소 빈도
CONF_APPLY       = 0.80    # 자동 적용 최소 신뢰도
CONF_PROPOSE     = 0.40    # 제안 최소 신뢰도
FP_RATIO         = 0.30    # bypass / (deny+bypass) 이 이 비율 이상이면 오탐 후보


class Event(NamedTuple):
    ts:       str
    decision: str   # deny | ask | allow_bypass
    tool:     str
    detail:   str


# ── 데이터 로드 ────────────────────────────────────────────────
def load_events() -> list:
    if not EVENTS_FILE.exists():
        return []
    events = []
    for line in EVENTS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
            events.append(Event(o["ts"], o["decision"], o["tool"], o["detail"]))
        except Exception:
            pass
    return events

def load_policy() -> dict:
    if not POLICY_FILE.exists():
        return {}
    try:
        return json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def load_learn() -> dict:
    defaults: dict = {
        "min_freq_propose": MIN_FREQ_PROPOSE,
        "min_freq_apply":   MIN_FREQ_APPLY,
        "confidence_apply": CONF_APPLY,
        "learned_patterns": [],
        "false_positives":  [],
        "history":          [],
    }
    if not LEARN_FILE.exists():
        return defaults
    try:
        d = json.loads(LEARN_FILE.read_text(encoding="utf-8"))
        defaults.update(d)
    except Exception:
        pass
    return defaults

def save_learn(cfg: dict):
    LEARN_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


# ── 패턴 추출 ──────────────────────────────────────────────────
def extract_raw(detail: str) -> str:
    """detail 에서 '— 이후'의 실제 명령/경로 부분 추출."""
    for sep in (" — ", " | ", ": "):
        if sep in detail:
            return detail.split(sep, 1)[-1].strip()
    return detail.strip()

# 가변값(경로·IP·해시)을 플레이스홀더로 치환
_VAR_SUBS = [
    (r"['\"]?/[\w/.\-]+['\"]?",    "<PATH>"),
    (r"~/[\w/.\-]+",               "<PATH>"),
    (r"https?://\S+",              "<URL>"),
    (r"\b\d{1,3}(\.\d{1,3}){3}\b","<IP>"),
    (r"\b[0-9a-f]{32,64}\b",       "<HASH>"),
    (r"\b\d{4,}\b",                "<NUM>"),
]

def normalize_cmd(cmd: str) -> str:
    c = cmd.lower().strip()
    c = re.sub(r"\s+", " ", c)
    for pat, repl in _VAR_SUBS:
        c = re.sub(pat, repl, c)
    return c.strip()

def cmd_signature(detail: str) -> str:
    """클러스터링용 안정적 시그니처 (앞 4 토큰)."""
    raw  = extract_raw(detail)
    norm = normalize_cmd(raw)
    toks = norm.split()
    return " ".join(toks[:4])


# ── 분석 ──────────────────────────────────────────────────────
class Analysis:
    def __init__(self, events: list):
        self.events   = events
        self.denies   = [e for e in events if e.decision == "deny"]
        self.asks     = [e for e in events if e.decision == "ask"]
        self.bypasses = [e for e in events if e.decision == "allow_bypass"]

    # ── 빈도 분석 ──
    def top_denied(self, n=10):
        return Counter(cmd_signature(e.detail) for e in self.denies).most_common(n)

    def top_asked(self, n=10):
        return Counter(cmd_signature(e.detail) for e in self.asks).most_common(n)

    # ── 오탐 후보: bypass 비율이 높은 패턴 ──
    def false_positive_candidates(self) -> list:
        bypass_cnt = Counter(cmd_signature(e.detail) for e in self.bypasses)
        deny_cnt   = Counter(cmd_signature(e.detail) for e in self.denies)
        result = []
        for sig, bc in bypass_cnt.items():
            dc = deny_cnt.get(sig, 0)
            total = dc + bc
            ratio = bc / total if total else 0
            if ratio >= FP_RATIO and total >= MIN_FREQ_PROPOSE:
                result.append((sig, dc, bc, round(ratio, 2)))
        return sorted(result, key=lambda x: -x[3])

    # ── 신규 패턴 후보: 빈번하지만 현재 정책에 없는 것 ──
    def new_pattern_candidates(self, policy: dict) -> list:
        # 현재 차단 규칙의 키워드 집합
        known: set = set()
        for p in policy.get("protected_paths", []):
            known.add(p.lower().split(".")[0].split("/")[0])

        freq = Counter(cmd_signature(e.detail) for e in self.denies)
        total_denies = len(self.denies) or 1
        result = []

        for sig, cnt in freq.most_common(40):
            if cnt < MIN_FREQ_PROPOSE:
                break
            first_tok = sig.split()[0] if sig.split() else ""
            # 이미 알려진 패턴이면 스킵 (단순 포함 체크)
            if any(first_tok in k or k in first_tok for k in known):
                continue
            # 신뢰도 = 빈도/전체 × 포화보정
            freq_score = min(1.0, cnt / (total_denies * 0.05 + 1))
            volume_score = min(1.0, cnt / MIN_FREQ_APPLY)
            confidence = round((freq_score + volume_score) / 2, 2)
            if confidence >= CONF_PROPOSE:
                result.append((sig, confidence, cnt))

        return sorted(result, key=lambda x: (-x[1], -x[2]))

    # ── 시간대별 이상 탐지 ──
    def hourly_spike(self) -> list:
        """특정 시간대에 평균 대비 2σ 이상 deny 폭증한 구간."""
        from collections import defaultdict
        import statistics
        buckets: dict = defaultdict(int)
        for e in self.denies:
            try:
                hour = e.ts[:13]  # "2026-05-28T14"
                buckets[hour] += 1
            except Exception:
                pass
        if len(buckets) < 3:
            return []
        counts = list(buckets.values())
        mean   = statistics.mean(counts)
        stdev  = statistics.stdev(counts) if len(counts) > 1 else 0
        threshold = mean + 2 * stdev
        spikes = [(h, c) for h, c in buckets.items() if c > threshold and c >= 5]
        return sorted(spikes, key=lambda x: -x[1])


# ── 정책 업데이트 ──────────────────────────────────────────────
def backup_policy():
    if not POLICY_FILE.exists():
        return
    POLICY_HISTORY.mkdir(parents=True, exist_ok=True)
    ts     = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = POLICY_HISTORY / f"harness-policy-{ts}.json"
    target.write_text(POLICY_FILE.read_text(encoding="utf-8"))
    return target

# ── Claude API / 폴백 정규식 생성 ─────────────────────────────
def _try_claude_regex(examples: list, signature: str) -> str | None:
    """Claude API(Haiku)로 예시 명령들에서 검증된 정규식 생성.
    API 키 없거나 실패 시 None 반환."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        ex_text = "\n".join(f"  - {e}" for e in examples[:8])
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": (
                "다음 bash 명령어들은 보안상 위험하여 차단해야 합니다.\n"
                f"공통 패턴을 잡는 Python 정규식 하나를 작성하세요.\n\n"
                f"예시:\n{ex_text}\n\n"
                "조건:\n"
                "- re.search(pattern, cmd.lower()) 로 사용\n"
                "- 정규식만 출력 (따옴표·설명 없이)\n"
                "- 너무 넓어서 정상 명령도 차단하면 안 됨\n"
                "- \\b 단어 경계 적극 활용\n\n"
                "패턴:"
            )}],
        )
        raw = resp.content[0].text.strip().strip("\"'`/")
        re.compile(raw)          # 컴파일 검증
        # 예시 중 절반 이상 매칭되는지 확인
        hits = sum(1 for e in examples if re.search(raw, e.lower()))
        if hits >= max(1, len(examples) // 2):
            return raw
    except Exception:
        pass
    return None


def _fallback_regex(signature: str, examples: list) -> str:
    """Claude API 없을 때 시그니처에서 기본 정규식 생성."""
    toks = signature.split()
    if not toks:
        return ""
    parts = []
    for tok in toks[:4]:
        if tok.startswith("<"):          # 플레이스홀더
            parts.append(r"\S+")
        elif re.match(r"^-[a-z]+$", tok):  # 단순 플래그
            # -rf → -[a-z]*r[a-z]*f 형식으로
            chars = tok[1:]
            if len(chars) <= 3:
                inner = "".join(f"[a-z]*{c}" for c in chars)
                parts.append(rf"-{inner}")
            else:
                parts.append(re.escape(tok))
        else:
            parts.append(rf"\b{re.escape(tok)}\b")
    return r"\s+".join(parts)


def apply_to_policy(rules: list, policy: dict) -> tuple:
    """생성된 regex 규칙을 learned_rules 에 추가. (updated_policy, added_count) 반환."""
    policy.setdefault("learned_rules", [])
    existing_pats = {r.get("pattern") for r in policy["learned_rules"]}
    added = 0
    for r in rules:
        pat = r.get("pattern", "")
        if pat and pat not in existing_pats:
            policy["learned_rules"].append(r)
            existing_pats.add(pat)
            added += 1
    return policy, added


# ── 출력 헬퍼 ─────────────────────────────────────────────────
B = "\033[1m"; DIM = "\033[2m"; RST = "\033[0m"
RED = "\033[31m"; YLW = "\033[33m"; GRN = "\033[32m"; CYN = "\033[36m"

def hr(n=56): return "─" * n

def bar_chart(cnt: int, total: int, width=24) -> str:
    filled = int(width * cnt / max(total, 1))
    return "█" * filled + "░" * (width - filled)


# ── 커맨드 핸들러 ──────────────────────────────────────────────
def cmd_summary(ana: "Analysis"):
    total = len(ana.events)
    if total == 0:
        print("📭 아직 이벤트가 없습니다. 클로드 코드로 작업하면 자동 수집됩니다.")
        return
    print(f"\n{B}=== AI 하네스 학습 분석 ==={RST}")
    print(f"  이벤트 {total}개  |  차단 {len(ana.denies)}  |  검토요청 {len(ana.asks)}  |  우회 {len(ana.bypasses)}")
    print(hr())

    top = ana.top_denied(5)
    if top:
        print(f"\n{B}▶ 상위 차단 패턴{RST}")
        for sig, cnt in top:
            print(f"  {cnt:4d}회  {bar_chart(cnt, top[0][1])}  {sig}")

    fps = ana.false_positive_candidates()
    if fps:
        print(f"\n{B}{YLW}▶ 오탐 후보 (bypass 비율 높음){RST}")
        for sig, dc, bc, ratio in fps[:5]:
            print(f"  bypass {ratio:.0%}  [차단 {dc} / 우회 {bc}]  {sig}")

    spikes = ana.hourly_spike()
    if spikes:
        print(f"\n{B}{RED}▶ 이상 급증 탐지{RST}")
        for hour, cnt in spikes[:3]:
            print(f"  {hour}  →  {cnt}건 (평균 대비 2σ 초과)")

    print()


def cmd_report(ana: "Analysis", policy: dict, learn: dict):
    cmd_summary(ana)

    top_ask = ana.top_asked(8)
    if top_ask:
        print(f"\n{B}▶ 상위 검토요청 패턴{RST}")
        for sig, cnt in top_ask:
            print(f"  {cnt:4d}회  {sig}")

    candidates = ana.new_pattern_candidates(policy)
    if candidates:
        print(f"\n{B}{CYN}▶ 신규 패턴 제안{RST}")
        print(f"  {'신뢰도':8}  {'빈도':6}  패턴")
        print(f"  {'-'*8}  {'-'*6}  {'-'*36}")
        for sig, conf, freq in candidates:
            flag = f" {GRN}← 자동적용 가능{RST}" if conf >= CONF_APPLY and freq >= MIN_FREQ_APPLY else ""
            print(f"  {conf:.2f}      {freq:4d}  {sig}{flag}")
    else:
        print(f"\n{GRN}✅ 추가할 신규 패턴 후보 없음{RST}")

    learned = learn.get("learned_patterns", [])
    if learned:
        print(f"\n{B}▶ 적용된 학습 규칙 ({len(learned)}개){RST}")
        for p in learned[-10:]:
            print(f"  • [{p.get('confidence','?'):.2f}] {p.get('signature','')}  ({p.get('applied','')[:10]})")

    hist = learn.get("history", [])
    if hist:
        print(f"\n{B}▶ 학습 이력{RST}")
        for h in hist[-5:]:
            print(f"  {h.get('ts','')[:19]}  +{h.get('applied',0)}개 패턴 적용")
    print()


def cmd_apply(ana: "Analysis", policy: dict, learn: dict):
    candidates = ana.new_pattern_candidates(policy)
    high_conf   = [(sig, conf, freq) for sig, conf, freq in candidates
                   if conf >= CONF_APPLY and freq >= MIN_FREQ_APPLY]

    if not high_conf:
        print(f"{GRN}✅ 자동 적용 임계값({CONF_APPLY:.0%} 신뢰도 / {MIN_FREQ_APPLY}회 빈도)을 "
              f"넘는 새 패턴이 없습니다.{RST}")
        return

    has_api = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"\n{B}정규식 생성 중 "
          f"({'Claude API' if has_api else '폴백 모드 — ANTHROPIC_API_KEY 없음'})...{RST}")

    # 시그니처별 실제 명령 예시 수집
    sig_examples: dict = {}
    for e in ana.denies:
        sig = cmd_signature(e.detail)
        sig_examples.setdefault(sig, [])
        raw = e.detail[:200]
        if raw not in sig_examples[sig]:
            sig_examples[sig].append(raw)

    new_rules = []
    for sig, conf, freq in high_conf:
        examples = sig_examples.get(sig, [sig])
        regex = _try_claude_regex(examples, sig) or _fallback_regex(sig, examples)
        if not regex:
            print(f"  ⚠ 패턴 생성 실패: {sig}")
            continue
        rule = {
            "pattern":     regex,
            "description": f"학습: {sig} ({freq}회 차단)",
            "action":      "deny",
            "confidence":  conf,
            "frequency":   freq,
            "scope":       "bash",
            "source":      "claude_api" if has_api else "fallback",
            "applied":     datetime.now(timezone.utc).isoformat(),
        }
        new_rules.append(rule)
        src = "🤖 API" if has_api else "📐 폴백"
        print(f"  + {src} [{conf:.2f}신뢰도  {freq}회]  {regex}")

    if not new_rules:
        print(f"{YLW}⚠ 적용할 유효한 규칙이 없습니다.{RST}")
        return

    backup_path = backup_policy()
    updated, added = apply_to_policy(new_rules, policy)
    POLICY_FILE.write_text(json.dumps(updated, indent=2, ensure_ascii=False))

    learn.setdefault("learned_patterns", []).extend(new_rules)
    learn.setdefault("history", []).append({
        "ts":      datetime.now(timezone.utc).isoformat(),
        "applied": added,
        "source":  "claude_api" if has_api else "fallback",
    })
    save_learn(learn)

    print(f"\n{GRN}✅ {added}개 정규식 규칙이 harness-policy.json[learned_rules] 에 추가됐습니다.")
    print(f"   pretooluse_gate.py 가 즉시 이 규칙을 적용합니다.{RST}")
    if backup_path:
        print(f"   백업: {backup_path}\n")


# ── 메인 ──────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="AI 하네스 자가 학습 엔진",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="예) python3 .claude/hooks/learn.py --apply"
    )
    ap.add_argument("--report", action="store_true", help="전체 분석 리포트")
    ap.add_argument("--apply",  action="store_true", help="고신뢰 패턴 자동 적용")
    ap.add_argument("--reset",  action="store_true", help="이벤트 로그 초기화")
    args = ap.parse_args()

    if args.reset:
        if EVENTS_FILE.exists():
            EVENTS_FILE.unlink()
            print("✅ 이벤트 로그를 초기화했습니다.")
        else:
            print("ℹ 이벤트 로그가 없습니다.")
        return

    events = load_events()
    policy = load_policy()
    learn  = load_learn()
    ana    = Analysis(events)

    if args.report:
        cmd_report(ana, policy, learn)
    elif args.apply:
        cmd_summary(ana)
        cmd_apply(ana, policy, learn)
    else:
        cmd_summary(ana)
        candidates = ana.new_pattern_candidates(policy)
        auto = [c for c in candidates if c[1] >= CONF_APPLY and c[2] >= MIN_FREQ_APPLY]
        if auto:
            print(f"{YLW}💡 {len(auto)}개의 고신뢰 패턴 발견. "
                  f"'--apply' 로 자동 적용하거나 '--report' 로 상세 확인하세요.{RST}")
        else:
            print(f"{DIM}전체 리포트: python3 .claude/hooks/learn.py --report{RST}")
        print()


if __name__ == "__main__":
    main()
