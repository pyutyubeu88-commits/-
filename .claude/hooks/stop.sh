#!/bin/bash
# Conway Stop Hook - memory.md 변경 시 자동으로 Git 동기화

CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TASKS_FILE="$CLAUDE_PROJECT_DIR/.conway/tasks.json"

# 미처리 작업 알림
if [ -f "$TASKS_FILE" ] && command -v python3 &>/dev/null; then
  python3 - <<'PYEOF'
import json, os
tasks_file = os.environ.get("CLAUDE_PROJECT_DIR", ".") + "/.conway/tasks.json"
try:
    with open(tasks_file) as f:
        tasks = json.load(f)
    pending = [t for t in tasks if t["status"] in ("pending", "queued")]
    if pending:
        print(f"[Conway] {len(pending)}개의 미처리 작업이 남아 있습니다.")
except:
    pass
PYEOF
fi

# memory.md 변경사항 자동 푸시 (다른 기기에서 사용 가능하도록)
if command -v git &>/dev/null && [ -d "$CLAUDE_PROJECT_DIR/.git" ]; then
  cd "$CLAUDE_PROJECT_DIR"
  REMOTE=$(git remote 2>/dev/null | head -1)
  if [ -n "$REMOTE" ]; then
    # memory.md가 변경되었는지 확인
    if ! git diff --quiet HEAD -- memory.md 2>/dev/null || git ls-files --others --exclude-standard memory.md | grep -q .; then
      git add memory.md 2>/dev/null || true
      git commit -m "chore: memory.md 자동 동기화 [Conway]" 2>/dev/null || true
      BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
      git push "$REMOTE" "$BRANCH" --quiet 2>/dev/null || true
      echo "[Conway] memory.md 변경사항이 원격에 동기화되었습니다."
    fi
  fi
fi
