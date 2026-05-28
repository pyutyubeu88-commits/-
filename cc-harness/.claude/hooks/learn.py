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

def apply_to_policy(patterns: list, policy: dict) -> dict:
    """학습된 패턴 시그니처를 learned_blocked_cmds 에 추가."""
    policy.setdefault("learned_blocked_cmds", [])
    existing = set(policy["learned_blocked_cmds"])
    added = 0
    for p in patterns:
        sig = p.get("signature", "")
        if sig and sig not in existing:
            policy["learned_blocked_cmds"].append(sig)
            existing.add(sig)
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
    to_apply = [
        {"signature": sig, "confidence": conf, "frequency": freq,
         "applied": datetime.now(timezone.utc).isoformat()}
        for sig, conf, freq in candidates
        if conf >= CONF_APPLY and freq >= MIN_FREQ_APPLY
    ]

    if not to_apply:
        print(f"{GRN}✅ 자동 적용 임계값({CONF_APPLY:.0%} 신뢰도 / {MIN_FREQ_APPLY}회 빈도)을 "
              f"넘는 새 패턴이 없습니다.{RST}")
        return

    print(f"\n{B}다음 패턴을 정책에 적용합니다:{RST}")
    for p in to_apply:
        print(f"  + [{p['confidence']:.2f}신뢰도  {p['frequency']}회]  {p['signature']}")

    backup_path = backup_policy()
    updated, added = apply_to_policy(to_apply, policy)
    POLICY_FILE.write_text(json.dumps(updated, indent=2, ensure_ascii=False))

    learn.setdefault("learned_patterns", []).extend(to_apply)
    learn.setdefault("history", []).append({
        "ts":      datetime.now(timezone.utc).isoformat(),
        "applied": added,
    })
    save_learn(learn)

    print(f"\n{GRN}✅ {added}개 패턴을 harness-policy.json 에 적용했습니다.{RST}")
    if backup_path:
        print(f"   백업: {backup_path}")
    print(f"\n{DIM}주의: learned_blocked_cmds 는 pretooluse_gate.py 가 참조하지 않으면 효과 없음.")
    print(f"gate 를 업데이트하거나 정책 파일을 수동 확인하세요.{RST}\n")


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
