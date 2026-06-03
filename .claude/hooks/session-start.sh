#!/bin/bash
set -euo pipefail

MEMORY_FILE="$CLAUDE_PROJECT_DIR/memory.md"

if [ ! -f "$MEMORY_FILE" ]; then
  exit 0
fi

CONTENT=$(cat "$MEMORY_FILE")
if [ -z "$CONTENT" ]; then
  exit 0
fi

cat <<EOF
<memory>
다음은 이전 세션에서 저장된 파일메모리입니다. 이 내용을 참고하여 컨텍스트를 유지하세요.

$CONTENT
</memory>
EOF
