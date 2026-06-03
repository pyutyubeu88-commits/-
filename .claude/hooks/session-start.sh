#!/bin/bash
set -euo pipefail

MEMORY_FILE="$CLAUDE_PROJECT_DIR/memory.md"
TASKS_FILE="$CLAUDE_PROJECT_DIR/.conway/tasks.json"

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
    print("\n> 위 작업들을 처리하려면 `python conway/cli.py result <id>` 또는 직접 처리 후 상태를 업데이트하세요.")
except Exception as e:
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
