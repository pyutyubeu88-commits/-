#!/usr/bin/env python3
"""SessionStart hook - Windows/Mac/Linux 공통 실행."""
import json, os, sys, subprocess

BASE = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def read_file(path):
    full = os.path.join(BASE, path)
    if not os.path.exists(full):
        return ""
    with open(full, encoding="utf-8") as f:
        return f.read()

def git_sync():
    """원격에서 최신 memory.md 동기화."""
    try:
        r = subprocess.run(["git", "remote"], cwd=BASE, capture_output=True, text=True)
        remote = r.stdout.strip().split("\n")[0] if r.stdout.strip() else ""
        if not remote:
            return
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=BASE, capture_output=True, text=True
        ).stdout.strip() or "main"
        subprocess.run(["git", "fetch", remote, branch, "--quiet"],
                       cwd=BASE, capture_output=True, timeout=10)
        local = subprocess.run(
            ["git", "show", "HEAD:memory.md"],
            cwd=BASE, capture_output=True, text=True
        ).stdout
        remote_content = subprocess.run(
            ["git", "show", f"{remote}/{branch}:memory.md"],
            cwd=BASE, capture_output=True, text=True
        ).stdout
        if remote_content and local != remote_content:
            subprocess.run(
                ["git", "checkout", f"{remote}/{branch}", "--", "memory.md"],
                cwd=BASE, capture_output=True
            )
    except Exception:
        pass

def pending_tasks():
    tasks_path = os.path.join(BASE, ".conway", "tasks.json")
    if not os.path.exists(tasks_path):
        return ""
    try:
        with open(tasks_path, encoding="utf-8") as f:
            tasks = json.load(f)
        pending = [t for t in tasks if t.get("status") in ("pending", "queued")]
        if not pending:
            return ""
        lines = [f"\n## Conway 미처리 작업 ({len(pending)}개)\n"]
        for t in pending:
            created = t.get("created", "")[:16].replace("T", " ")
            lines.append(f"- **[{t['id']}]** {t['title']} ({created}) - {t.get('source','?')}")
            if t.get("description"):
                lines.append(f"  └ {t['description'][:100]}")
        lines.append("\n> `python conway/cli.py result <id>` 로 결과 확인")
        return "\n".join(lines)
    except Exception:
        return ""

def main():
    git_sync()
    memory = read_file("memory.md")
    tasks = pending_tasks()

    if not memory and not tasks:
        return

    print("<conway-context>")
    if memory:
        print("## 파일 메모리 (memory.md)\n")
        print(memory)
    if tasks:
        print(tasks)
    print("</conway-context>")

if __name__ == "__main__":
    main()
