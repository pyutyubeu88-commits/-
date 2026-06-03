#!/usr/bin/env python3
"""Conway MCP Server - memory.md와 작업 큐를 모든 Claude 환경에 노출."""

import json
import sys
import os
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def abs_path(rel):
    return os.path.join(BASE_DIR, rel)

def read_memory():
    path = abs_path("memory.md")
    if not os.path.exists(path):
        return "(메모리 없음)"
    with open(path) as f:
        return f.read()

def append_memory(note, section="메모"):
    path = abs_path("memory.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "a") as f:
        f.write(f"\n\n### [{timestamp}] {section}\n{note}")
    return f"저장됨: [{section}] {note[:50]}..."

def get_tasks(status_filter=None):
    path = abs_path(".conway/tasks.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        tasks = json.load(f)
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    return tasks

def add_task(title, description="", source="mcp"):
    path = abs_path(".conway/tasks.json")
    tasks = []
    if os.path.exists(path):
        with open(path) as f:
            tasks = json.load(f)
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "source": source,
        "extension": None,
        "payload": {},
        "status": "queued",
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "result": None
    }
    tasks.append(task)
    with open(path, "w") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    return task

def get_task_result(task_id):
    result_file = abs_path(f".conway/results/{task_id}.md")
    if os.path.exists(result_file):
        with open(result_file) as f:
            return f.read()
    tasks = get_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task and task.get("result"):
        return task["result"]
    return "(결과 없음)"

# MCP 도구 정의
TOOLS = [
    {
        "name": "memory_read",
        "description": "이전 세션들의 중요 정보가 저장된 memory.md를 읽습니다. 세션 시작 시 항상 호출하세요.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "memory_write",
        "description": "중요한 정보를 memory.md에 기록합니다. 결정사항, 진행 상황, 사용자 선호도 등을 저장하세요.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "기록할 내용"
                },
                "section": {
                    "type": "string",
                    "description": "섹션 이름 (예: 결정사항, 진행중, 메모)",
                    "default": "메모"
                }
            },
            "required": ["note"]
        }
    },
    {
        "name": "tasks_list",
        "description": "Conway 작업 큐의 작업 목록을 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "필터: pending, queued, done, processing (생략 시 전체)",
                    "enum": ["pending", "queued", "done", "processing", "failed"]
                }
            }
        }
    },
    {
        "name": "task_add",
        "description": "Conway 작업 큐에 새 작업을 추가합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "작업 제목"
                },
                "description": {
                    "type": "string",
                    "description": "작업 상세 설명"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "task_result",
        "description": "특정 작업의 처리 결과를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "작업 ID"
                }
            },
            "required": ["task_id"]
        }
    }
]

def handle_tool_call(name, arguments):
    if name == "memory_read":
        content = read_memory()
        return [{"type": "text", "text": content}]

    elif name == "memory_write":
        note = arguments.get("note", "")
        section = arguments.get("section", "메모")
        result = append_memory(note, section)
        return [{"type": "text", "text": f"✅ memory.md에 저장됨\n섹션: {section}\n내용: {note[:100]}"}]

    elif name == "tasks_list":
        status = arguments.get("status")
        tasks = get_tasks(status)
        if not tasks:
            return [{"type": "text", "text": "작업이 없습니다."}]
        lines = [f"총 {len(tasks)}개 작업:\n"]
        for t in reversed(tasks[-20:]):
            icon = {"pending": "⏳", "queued": "📥", "done": "✅", "processing": "⚙️", "failed": "❌"}.get(t["status"], "?")
            created = t.get("created", "")[:16].replace("T", " ")
            lines.append(f"{icon} [{t['id']}] {t['title']}")
            lines.append(f"   상태: {t['status']} | {created} | {t.get('source', '?')}")
            if t.get("description"):
                lines.append(f"   {t['description'][:80]}")
            lines.append("")
        return [{"type": "text", "text": "\n".join(lines)}]

    elif name == "task_add":
        title = arguments.get("title", "")
        description = arguments.get("description", "")
        task = add_task(title, description)
        return [{"type": "text", "text": f"✅ 작업 추가됨\nID: {task['id']}\n제목: {title}"}]

    elif name == "task_result":
        task_id = arguments.get("task_id", "")
        result = get_task_result(task_id)
        return [{"type": "text", "text": f"작업 [{task_id}] 결과:\n\n{result}"}]

    else:
        return [{"type": "text", "text": f"알 수 없는 도구: {name}"}]

def send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        req_id = req.get("id")

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "conway-memory", "version": "1.0.0"}
                }
            })

        elif method == "notifications/initialized":
            pass  # 응답 불필요

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS}
            })

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                content = handle_tool_call(tool_name, arguments)
                send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": content, "isError": False}
                })
            except Exception as e:
                send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"오류: {e}"}],
                        "isError": True
                    }
                })

        elif req_id is not None:
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })

if __name__ == "__main__":
    main()
