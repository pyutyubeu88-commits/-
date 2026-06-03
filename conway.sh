#!/bin/bash
# Conway 시스템 관리 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.conway/server.pid"

case "${1:-help}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Conway 서버가 이미 실행 중입니다 (PID: $(cat "$PID_FILE"))"
      exit 0
    fi
    echo "Conway 서버 시작 중..."
    nohup python3 "$SCRIPT_DIR/conway/server.py" > "$SCRIPT_DIR/.conway/logs/server.log" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ Conway 서버 시작됨 (PID: $(cat "$PID_FILE"), 포트: 8765)"
      echo "   대시보드: conway_dashboard.html 브라우저에서 열기"
    else
      echo "❌ 서버 시작 실패. 로그 확인: .conway/logs/server.log"
    fi
    ;;

  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "✅ Conway 서버 종료됨"
      else
        echo "서버가 실행 중이 아닙니다"
        rm -f "$PID_FILE"
      fi
    else
      echo "서버가 실행 중이 아닙니다"
    fi
    ;;

  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ Conway 서버 실행 중 (PID: $(cat "$PID_FILE"))"
      python3 "$SCRIPT_DIR/conway/cli.py" status
    else
      echo "❌ Conway 서버 미실행"
      python3 "$SCRIPT_DIR/conway/cli.py" status
    fi
    ;;

  restart)
    $0 stop
    sleep 1
    $0 start
    ;;

  logs)
    tail -f "$SCRIPT_DIR/.conway/logs/server.log"
    ;;

  *)
    echo "Conway 시스템 관리"
    echo ""
    echo "사용법: ./conway.sh [명령]"
    echo ""
    echo "서버 관리:"
    echo "  start    Conway 서버 시작 (백그라운드)"
    echo "  stop     Conway 서버 종료"
    echo "  status   서버 상태 + 작업 현황"
    echo "  restart  서버 재시작"
    echo "  logs     실시간 로그 보기"
    echo ""
    echo "작업 관리 (CLI):"
    echo "  python conway/cli.py add '제목' '설명'   작업 추가"
    echo "  python conway/cli.py tasks               작업 목록"
    echo "  python conway/cli.py result <id>         결과 보기"
    echo "  python conway/cli.py memory              메모리 보기"
    echo "  python conway/cli.py note '내용'         메모리에 기록"
    echo ""
    echo "웹훅 테스트:"
    echo "  curl -X POST http://localhost:8765/webhook \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"title\": \"테스트 작업\", \"description\": \"설명\"}'"
    ;;
esac
