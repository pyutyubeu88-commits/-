#!/usr/bin/env python3
"""Conway Server - Webhook receiver + REST API + Agent runner."""

import json
import os
import sys
import uuid
import threading
import time
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, ".conway", "config.json")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

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
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_event(event_type, data):
    cfg = load_config()
    events = read_json(cfg["events_file"], [])
    events.append({
        "id": str(uuid.uuid4())[:8],
        "type": event_type,
        "time": datetime.now().isoformat(),
        "data": data
    })
    events = events[-cfg.get("max_events", 500):]
    write_json(cfg["events_file"], events)

def add_task(title, description="", source="api", extension=None, payload=None):
    cfg = load_config()
    tasks = read_json(cfg["tasks_file"], [])
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "source": source,
        "extension": extension,
        "payload": payload or {},
        "status": "pending",
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "result": None
    }
    tasks.append(task)
    write_json(cfg["tasks_file"], tasks)
    log_event("task_created", {"id": task["id"], "title": title, "source": source})
    return task

def update_task(task_id, **kwargs):
    cfg = load_config()
    tasks = read_json(cfg["tasks_file"], [])
    for t in tasks:
        if t["id"] == task_id:
            t.update(kwargs)
            t["updated"] = datetime.now().isoformat()
            break
    write_json(cfg["tasks_file"], tasks)

def run_agent(task):
    """Process a task using Claude API or Claude Code CLI."""
    cfg = load_config()
    if not cfg.get("agent_enabled"):
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Try Claude Code CLI first (no API key needed)
    if not api_key:
        result_file = abs_path(f".conway/results/{task['id']}.md")
        prompt = f"# Conway 작업\n\n**제목**: {task['title']}\n\n**설명**: {task['description']}\n\n작업을 처리하고 결과를 한국어로 작성하세요."
        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True, text=True, timeout=120,
                cwd=BASE_DIR
            )
            output = result.stdout.strip() if result.returncode == 0 else f"오류: {result.stderr}"
        except Exception as e:
            output = f"Claude CLI 실행 실패: {e}\n\nAPI 키를 설정하거나 Claude Code CLI를 사용하세요."
        with open(result_file, "w") as f:
            f.write(output)
        return output

    # Use Anthropic SDK if API key available
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Load memory for context
        memory_path = abs_path(cfg["memory_file"])
        memory_content = ""
        if os.path.exists(memory_path):
            with open(memory_path) as f:
                memory_content = f.read()

        # Load extension if specified
        extension_prompt = ""
        if task.get("extension"):
            ext_path = abs_path(f".conway/extensions/{task['extension']}.cnw.py")
            if os.path.exists(ext_path):
                with open(ext_path) as f:
                    extension_prompt = f"\n\n## 확장 모듈 지시사항\n{f.read()}"

        system = f"""당신은 Conway AI 에이전트입니다. 백그라운드에서 자율적으로 작업을 처리합니다.

## 프로젝트 메모리
{memory_content}
{extension_prompt}

작업을 처리하고 결과를 명확하게 작성하세요."""

        msg = client.messages.create(
            model=cfg.get("agent_model", "claude-sonnet-4-6"),
            max_tokens=4096,
            system=system,
            messages=[{
                "role": "user",
                "content": f"**작업**: {task['title']}\n\n**상세**: {task['description']}\n\n**페이로드**: {json.dumps(task.get('payload', {}), ensure_ascii=False)}"
            }]
        )
        output = msg.content[0].text
        result_file = abs_path(f".conway/results/{task['id']}.md")
        with open(result_file, "w") as f:
            f.write(output)
        return output

    except ImportError:
        return "anthropic 패키지 미설치: pip install anthropic"
    except Exception as e:
        return f"에이전트 오류: {e}"

def agent_loop():
    """Background agent loop - polls for pending tasks and processes them."""
    print("[Conway Agent] 루프 시작", flush=True)
    while True:
        try:
            cfg = load_config()
            tasks = read_json(cfg["tasks_file"], [])
            pending = [t for t in tasks if t["status"] == "pending"]

            for task in pending:
                print(f"[Conway Agent] 작업 처리 중: {task['id']} - {task['title']}", flush=True)
                update_task(task["id"], status="processing")
                log_event("task_processing", {"id": task["id"]})

                result = run_agent(task)

                if result:
                    update_task(task["id"], status="done", result=result)
                    log_event("task_done", {"id": task["id"], "result_preview": result[:200]})
                    print(f"[Conway Agent] 완료: {task['id']}", flush=True)
                else:
                    update_task(task["id"], status="queued",
                               result="에이전트 비활성화 - Claude 세션에서 처리 필요")

        except Exception as e:
            print(f"[Conway Agent] 오류: {e}", flush=True)

        time.sleep(30)


class ConwayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_cors()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        cfg = load_config()

        if path == "/status":
            tasks = read_json(cfg["tasks_file"], [])
            self.send_json({
                "status": "running",
                "version": "1.0.0",
                "uptime": "active",
                "tasks": {
                    "total": len(tasks),
                    "pending": len([t for t in tasks if t["status"] == "pending"]),
                    "processing": len([t for t in tasks if t["status"] == "processing"]),
                    "done": len([t for t in tasks if t["status"] == "done"]),
                    "queued": len([t for t in tasks if t["status"] == "queued"]),
                }
            })

        elif path == "/tasks":
            tasks = read_json(cfg["tasks_file"], [])
            self.send_json(tasks)

        elif path.startswith("/task/"):
            task_id = path.split("/task/")[1]
            tasks = read_json(cfg["tasks_file"], [])
            task = next((t for t in tasks if t["id"] == task_id), None)
            if task:
                self.send_json(task)
            else:
                self.send_json({"error": "Task not found"}, 404)

        elif path == "/memory":
            memory_path = abs_path(cfg["memory_file"])
            content = open(memory_path).read() if os.path.exists(memory_path) else ""
            self.send_json({"content": content})

        elif path == "/events":
            qs = parse_qs(parsed.query)
            limit = int(qs.get("limit", [50])[0])
            events = read_json(cfg["events_file"], [])
            self.send_json(events[-limit:])

        elif path == "/extensions":
            ext_dir = abs_path(cfg["extensions_dir"])
            exts = []
            if os.path.exists(ext_dir):
                for f in os.listdir(ext_dir):
                    if f.endswith(".cnw.py"):
                        name = f[:-7]
                        with open(os.path.join(ext_dir, f)) as fp:
                            first_line = fp.readline().strip()
                        exts.append({"name": name, "description": first_line.lstrip("#").strip()})
            self.send_json(exts)

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        body = self.read_body()
        cfg = load_config()

        if path in ("/task", "/webhook"):
            title = body.get("title", body.get("event", "외부 트리거"))
            description = body.get("description", body.get("body", ""))
            source = body.get("source", "webhook" if path == "/webhook" else "api")
            extension = body.get("extension")
            payload = body.get("payload", body)

            task = add_task(title, description, source, extension, payload)
            self.send_json({"ok": True, "task": task}, 201)

        elif path == "/memory":
            content = body.get("content", "")
            mode = body.get("mode", "append")
            memory_path = abs_path(cfg["memory_file"])

            if mode == "append":
                with open(memory_path, "a") as f:
                    f.write(f"\n\n{content}")
            else:
                with open(memory_path, "w") as f:
                    f.write(content)

            log_event("memory_updated", {"mode": mode, "chars": len(content)})
            self.send_json({"ok": True})

        elif path == "/memory/note":
            note = body.get("note", "")
            section = body.get("section", "메모")
            memory_path = abs_path(cfg["memory_file"])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(memory_path, "a") as f:
                f.write(f"\n\n### [{timestamp}] {section}\n{note}")
            log_event("memory_note", {"section": section})
            self.send_json({"ok": True})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        cfg = load_config()

        if path.startswith("/task/"):
            task_id = path.split("/task/")[1]
            tasks = read_json(cfg["tasks_file"], [])
            tasks = [t for t in tasks if t["id"] != task_id]
            write_json(cfg["tasks_file"], tasks)
            log_event("task_deleted", {"id": task_id})
            self.send_json({"ok": True})
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    cfg = load_config()
    port = cfg.get("port", 8765)

    # Start agent loop in background thread
    agent_thread = threading.Thread(target=agent_loop, daemon=True)
    agent_thread.start()

    server = HTTPServer(("0.0.0.0", port), ConwayHandler)
    log_event("server_start", {"port": port})
    print(f"[Conway Server] http://0.0.0.0:{port} 에서 실행 중", flush=True)
    print(f"[Conway Server] 종료하려면 Ctrl+C", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Conway Server] 종료 중...", flush=True)
        log_event("server_stop", {})


if __name__ == "__main__":
    main()
