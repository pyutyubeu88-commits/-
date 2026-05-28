#!/bin/bash
# ================================================================
# AI 하네스 — 클로드 코드 설치 스크립트
# 사용법: ./install.sh [대상_프로젝트_경로]
#         경로 생략 시 현재 디렉토리에 설치
# ================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

TARGET="${1:-$PWD}"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI 하네스 — 클로드 코드 설치            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 사전 점검 ─────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}❌ python3 가 필요합니다. 먼저 설치하세요.${NC}"
  exit 1
fi
echo -e "${GREEN}✅ python3 확인${NC}"

if ! command -v claude &>/dev/null; then
  echo -e "${YELLOW}⚠ claude CLI 가 감지되지 않았습니다. 클로드 코드가 설치돼 있는지 확인하세요.${NC}"
  echo -e "${YELLOW}  (설치는 계속 진행합니다)${NC}"
fi

echo -e "${CYAN}대상 프로젝트: $TARGET${NC}"
echo ""

# ── 디렉토리 생성 ─────────────────────────────────────────────
mkdir -p "$TARGET/.claude/hooks"

# ── 파일 복사 ─────────────────────────────────────────────────
cp "$SRC/.claude/hooks/pretooluse_gate.py"      "$TARGET/.claude/hooks/"
cp "$SRC/.claude/hooks/posttooluse_validate.py" "$TARGET/.claude/hooks/"
cp "$SRC/.claude/hooks/posttooluse_review.py"   "$TARGET/.claude/hooks/"
cp "$SRC/.claude/hooks/learn.py"                "$TARGET/.claude/hooks/"
cp "$SRC/.claude/hooks/test_gate.py"            "$TARGET/.claude/hooks/"
cp "$SRC/.claude/harness-policy.json"           "$TARGET/.claude/"
echo -e "${GREEN}✅ hook 스크립트 복사 완료${NC}"

# ── harness-learn.json (없으면 생성) ─────────────────────────
LEARN_FILE="$TARGET/.claude/harness-learn.json"
if [ ! -f "$LEARN_FILE" ]; then
  cat > "$LEARN_FILE" << 'EOF'
{
  "_comment": "AI 하네스 자가 학습 설정 — learn.py 가 읽고 업데이트합니다",
  "min_freq_propose": 3,
  "min_freq_apply": 10,
  "confidence_apply": 0.80,
  "learned_patterns": [],
  "false_positives": [],
  "history": []
}
EOF
  echo -e "${GREEN}✅ harness-learn.json 생성${NC}"
fi

# ── CLAUDE.md 설치 (프로젝트 루트 — 클로드 코드가 자동으로 읽음) ──
ROOT_CLAUDE="$TARGET/CLAUDE.md"
if [ -f "$ROOT_CLAUDE" ]; then
  if grep -q "AI 하네스 적용 중" "$ROOT_CLAUDE"; then
    echo -e "${YELLOW}⚠ CLAUDE.md 에 하네스 규칙이 이미 있음 — 건너뜀${NC}"
  else
    echo -e "${YELLOW}⚠ 기존 CLAUDE.md 발견 — 하네스 규칙을 끝에 추가${NC}"
    echo "" >> "$ROOT_CLAUDE"
    echo "---" >> "$ROOT_CLAUDE"
    echo "" >> "$ROOT_CLAUDE"
    cat "$SRC/.claude/CLAUDE.md" >> "$ROOT_CLAUDE"
  fi
else
  cp "$SRC/.claude/CLAUDE.md" "$ROOT_CLAUDE"
  echo -e "${GREEN}✅ CLAUDE.md 생성 (프로젝트 루트)${NC}"
fi

# ── settings.json 병합 (기존 설정 보존) ──────────────────────
SETTINGS="$TARGET/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  echo -e "${YELLOW}⚠ 기존 settings.json 발견 — 백업 후 병합${NC}"
  cp "$SETTINGS" "$SETTINGS.bak-$(date +%s)"
  python3 - "$SETTINGS" "$SRC/.claude/settings.json" << 'PYEOF'
import json, sys
target_path, src_path = sys.argv[1], sys.argv[2]
with open(target_path) as f: target = json.load(f)
with open(src_path) as f: src = json.load(f)
target.setdefault("hooks", {})
skipped = 0
for event, groups in src["hooks"].items():
    target["hooks"].setdefault(event, [])
    existing_cmds = {h["command"] for g in target["hooks"][event] for h in g.get("hooks", [])}
    for group in groups:
        new_cmds = {h["command"] for h in group.get("hooks", [])}
        if new_cmds & existing_cmds:
            skipped += 1
        else:
            target["hooks"][event].append(group)
with open(target_path, "w") as f: json.dump(target, f, indent=2, ensure_ascii=False)
print(f"  병합 완료 (중복 {skipped}건 건너뜀)" if skipped else "  병합 완료")
PYEOF
else
  cp "$SRC/.claude/settings.json" "$SETTINGS"
  echo -e "${GREEN}✅ settings.json 생성${NC}"
fi

# ── 검증 ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}── 설치 검증 (게이트 자가 테스트) ──${NC}"
cd "$TARGET"
if python3 .claude/hooks/test_gate.py 2>&1 | tail -1; then
  echo -e "${GREEN}✅ 게이트 정상 작동${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ 설치 완료!                            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "다음 단계:"
echo "  1. 클로드 코드를 재시작하면 hook이 활성화됩니다"
echo "  2. 정책 수정: $TARGET/.claude/harness-policy.json"
echo "  3. 감사 로그: $TARGET/.claude/harness-audit.jsonl"
echo "  4. 일시 허용: 명령어 끝에 '# [harness-allow]' 주석 추가"
echo ""
echo "자가 학습:"
echo "  python3 .claude/hooks/learn.py             # 분석 요약"
echo "  python3 .claude/hooks/learn.py --report    # 전체 리포트"
echo "  python3 .claude/hooks/learn.py --apply     # 고신뢰 패턴 자동 적용"
echo ""
echo "테스트: 클로드 코드에서 'rm -rf 로 임시폴더 지워줘' 라고 해보세요 → 차단됨"
