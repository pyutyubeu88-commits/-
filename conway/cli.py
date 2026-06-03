#!/usr/bin/env python3
"""Conway CLI - 커맨드라인 관리 도구."""

import sys
import json
import os
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def abs_path(rel):
    return os.path.join(BASE_DIR, rel)

def read_json(path, default=None):
    full = abs_path(path)
    if not os.path.exists(full):
        return default if default is not None else []
    with open(full) as f:
        return json.load(f)

def write_json(path, data):
    full = abs_path(path)
    with open(full, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fmt_time(iso):
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%m/%d %H:%M")
    except:
        return iso

STATUS_ICON = {
    "pending": "⏳",
    "processing": "⚙️ ",
    "done": "✅",
    "queued": "📥",
    "failed": "❌"
}

def cmd_status():
    tasks = read_json(".conway/tasks.json", [])
    events = read_json(".conway/events.json", [])
    pending = [t for t in tasks if t["status"] in ("pending", "processing")]
    done = [t for t in tasks if t["status"] == "done"]
    queued = [t for t in tasks if t["status"] == "queued"]

    print("=" * 50)
    print("  Conway 시스템 상태")
    print("=" * 50)
    print(f"  전체 작업:  {len(tasks)}")
    print(f"  처리 중:    {len(pending)} ⏳")
    print(f"  완료:       {len(done)} ✅")
    print(f"  대기 중:    {len(queued)} 📥")
    print(f"  이벤트:     {len(events)}")
    print("=" * 50)

def cmd_tasks(filter_status=None):
    tasks = read_json(".conway/tasks.json", [])
    if filter_status:
        tasks = [t for t in tasks if t["status"] == filter_status]
    if not tasks:
        print("작업이 없습니다.")
        return
    print(f"{'ID':8} {'상태':10} {'시간':12} {'제목'}")
    print("-" * 60)
    for t in reversed(tasks[-20:]):
        icon = STATUS_ICON.get(t["status"], "?")
        print(f"{t['id']:8} {icon}{t['status']:8} {fmt_time(t['created']):12} {t['title'][:35]}")

def cmd_add(title, description=""):
    tasks = read_json(".conway/tasks.json", [])
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "source": "cli",
        "extension": None,
        "payload": {},
        "status": "queued",
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "result": None
    }
    tasks.append(task)
    write_json(".conway/tasks.json", tasks)
    print(f"✅ 작업 추가됨: [{task['id']}] {title}")

def cmd_result(task_id):
    tasks = read_json(".conway/tasks.json", [])
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        print(f"작업을 찾을 수 없음: {task_id}")
        return
    print(f"[{task['id']}] {task['title']}")
    print(f"상태: {task['status']} | 생성: {fmt_time(task['created'])}")
    print("-" * 50)
    result_file = abs_path(f".conway/results/{task_id}.md")
    if os.path.exists(result_file):
        with open(result_file) as f:
            print(f.read())
    elif task.get("result"):
        print(task["result"])
    else:
        print("(결과 없음)")

def cmd_memory():
    memory_path = abs_path("memory.md")
    if not os.path.exists(memory_path):
        print("memory.md 파일이 없습니다.")
        return
    with open(memory_path) as f:
        print(f.read())

def cmd_note(note, section="메모"):
    memory_path = abs_path("memory.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(memory_path, "a") as f:
        f.write(f"\n\n### [{timestamp}] {section}\n{note}")
    print(f"✅ 메모리에 기록됨: [{section}] {note}")

def cmd_events(limit=15):
    events = read_json(".conway/events.json", [])
    if not events:
        print("이벤트 없음")
        return
    print(f"{'시간':16} {'타입':20} {'데이터'}")
    print("-" * 70)
    for e in reversed(events[-limit:]):
        t = fmt_time(e["time"])
        data_str = json.dumps(e["data"], ensure_ascii=False)[:40]
        print(f"{t:16} {e['type']:20} {data_str}")

def cmd_clear_done():
    tasks = read_json(".conway/tasks.json", [])
    before = len(tasks)
    tasks = [t for t in tasks if t["status"] not in ("done",)]
    write_json(".conway/tasks.json", tasks)
    print(f"✅ {before - len(tasks)}개 완료 작업 삭제됨")

def cmd_help():
    print("""Conway CLI 사용법:
  python conway/cli.py status              - 시스템 상태
  python conway/cli.py tasks               - 전체 작업 목록
  python conway/cli.py tasks pending       - 대기 중 작업
  python conway/cli.py add "제목" "설명"  - 작업 추가
  python conway/cli.py result <id>         - 작업 결과 보기
  python conway/cli.py memory              - 메모리 보기
  python conway/cli.py note "내용" "섹션" - 메모리에 기록
  python conway/cli.py events              - 이벤트 로그
  python conway/cli.py clear               - 완료 작업 삭제
""")

def main():
    args = sys.argv[1:]
    if not args or args[0] == "help":
        cmd_help()
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "tasks":
        cmd_tasks(args[1] if len(args) > 1 else None)
    elif args[0] == "add":
        cmd_add(args[1] if len(args) > 1 else "새 작업",
                args[2] if len(args) > 2 else "")
    elif args[0] == "result":
        cmd_result(args[1] if len(args) > 1 else "")
    elif args[0] == "memory":
        cmd_memory()
    elif args[0] == "note":
        cmd_note(args[1] if len(args) > 1 else "",
                 args[2] if len(args) > 2 else "메모")
    elif args[0] == "events":
        cmd_events()
    elif args[0] == "clear":
        cmd_clear_done()
    else:
        print(f"알 수 없는 명령: {args[0]}")
        cmd_help()

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    main()
