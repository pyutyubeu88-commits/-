#!/bin/bash
# Conway Stop Hook - 세션 종료 시 메모리 업데이트 안내

TASKS_FILE="$CLAUDE_PROJECT_DIR/.conway/tasks.json"

# 완료된 작업이 있으면 알림
if [ -f "$TASKS_FILE" ] && command -v python3 &>/dev/null; then
  python3 - <<'PYEOF'
import json, os

tasks_file = os.environ.get("CLAUDE_PROJECT_DIR", ".") + "/.conway/tasks.json"
try:
    with open(tasks_file) as f:
        tasks = json.load(f)
    pending = [t for t in tasks if t["status"] in ("pending", "queued")]
    if pending:
        print(f"\n[Conway] {len(pending)}개의 미처리 작업이 있습니다. memory.md에 진행 상황을 기록해두세요.")
except:
    pass
PYEOF
fi
