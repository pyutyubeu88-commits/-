#!/bin/bash
set -euo pipefail

MEMORY_FILE="$CLAUDE_PROJECT_DIR/memory.md"
TASKS_FILE="$CLAUDE_PROJECT_DIR/.conway/tasks.json"

# --- 원격에서 최신 memory.md 동기화 (다른 기기에서 변경된 내용 반영) ---
if command -v git &>/dev/null && [ -d "$CLAUDE_PROJECT_DIR/.git" ]; then
  cd "$CLAUDE_PROJECT_DIR"
  REMOTE=$(git remote 2>/dev/null | head -1)
  if [ -n "$REMOTE" ]; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
    git fetch "$REMOTE" "$BRANCH" --quiet 2>/dev/null || true
    # 원격에 더 최신 memory.md가 있으면 가져옴
    LOCAL_HASH=$(git show HEAD:memory.md 2>/dev/null | sha256sum | cut -d' ' -f1 || echo "")
    REMOTE_HASH=$(git show "$REMOTE/$BRANCH:memory.md" 2>/dev/null | sha256sum | cut -d' ' -f1 || echo "")
    if [ -n "$REMOTE_HASH" ] && [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
      git checkout "$REMOTE/$BRANCH" -- memory.md 2>/dev/null || true
    fi
  fi
fi

# --- 메모리 로드 ---
MEMORY_CONTENT=""
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_CONTENT=$(cat "$MEMORY_FILE")
fi

# --- 미처리 작업 로드 ---
PENDING_TASKS=""
if [ -f "$TASKS_FILE" ] && command -v python3 &>/dev/null; then
  PENDING_TASKS=$(python3 - <<'PYEOF'
import json, os, sys

tasks_file = os.environ.get("CLAUDE_PROJECT_DIR", ".") + "/.conway/tasks.json"
try:
    with open(tasks_file) as f:
        tasks = json.load(f)
    pending = [t for t in tasks if t["status"] in ("pending", "queued")]
    if not pending:
        sys.exit(0)
    print(f"\n## Conway 미처리 작업 ({len(pending)}개)\n")
    for t in pending:
        created = t.get("created", "")[:16].replace("T", " ")
        print(f"- **[{t['id']}]** {t['title']} ({created}) - 출처: {t.get('source','?')}")
        if t.get("description"):
            print(f"  └ {t['description'][:100]}")
    print("\n> 위 작업들을 처리하려면 직접 확인하거나 `python conway/cli.py result <id>`를 사용하세요.")
except Exception:
    pass
PYEOF
  )
fi

# --- 출력 ---
if [ -z "$MEMORY_CONTENT" ] && [ -z "$PENDING_TASKS" ]; then
  exit 0
fi

echo "<conway-context>"

if [ -n "$MEMORY_CONTENT" ]; then
  echo "## 파일 메모리 (memory.md)"
  echo ""
  echo "$MEMORY_CONTENT"
fi

if [ -n "$PENDING_TASKS" ]; then
  echo "$PENDING_TASKS"
fi

echo "</conway-context>"
