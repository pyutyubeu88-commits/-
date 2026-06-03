#!/usr/bin/env python3
"""Conway Sync - memory.md 변경사항을 Git으로 자동 동기화."""

import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, check=True):
    return subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, check=check)

def is_git_repo():
    r = run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
    return r.returncode == 0

def has_remote():
    r = run(["git", "remote"], check=False)
    return bool(r.stdout.strip())

def memory_changed():
    r = run(["git", "diff", "--name-only", "HEAD", "--", "memory.md"], check=False)
    if r.stdout.strip():
        return True
    r2 = run(["git", "status", "--porcelain", "memory.md"], check=False)
    return bool(r2.stdout.strip())

def pull():
    """원격에서 최신 memory.md를 가져옵니다."""
    if not is_git_repo() or not has_remote():
        return False, "git 원격 없음"
    try:
        branch = run(["git", "branch", "--show-current"]).stdout.strip()
        run(["git", "fetch", "origin", branch])
        # memory.md만 원격 버전으로 갱신
        run(["git", "checkout", f"origin/{branch}", "--", "memory.md"])
        return True, f"memory.md를 origin/{branch}에서 업데이트"
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def push():
    """memory.md 변경사항을 원격에 커밋+푸시합니다."""
    if not is_git_repo() or not has_remote():
        return False, "git 원격 없음"
    if not memory_changed():
        return True, "변경 없음"
    try:
        run(["git", "add", "memory.md"])
        run(["git", "commit", "-m", "chore: memory.md 자동 동기화 [Conway]"])
        branch = run(["git", "branch", "--show-current"]).stdout.strip()
        run(["git", "push", "origin", branch])
        return True, "memory.md 푸시 완료"
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def export_for_mobile(output_path=None):
    """모바일/Claude Projects용 요약 파일을 생성합니다."""
    memory_path = os.path.join(BASE_DIR, "memory.md")
    tasks_path = os.path.join(BASE_DIR, ".conway", "tasks.json")

    if not os.path.exists(memory_path):
        return False, "memory.md 없음"

    with open(memory_path) as f:
        memory = f.read()

    # 미처리 작업 요약
    task_summary = ""
    if os.path.exists(tasks_path):
        import json
        with open(tasks_path) as f:
            tasks = json.load(f)
        pending = [t for t in tasks if t["status"] in ("pending", "queued")]
        if pending:
            task_summary = f"\n\n## 미처리 작업 ({len(pending)}개)\n"
            for t in pending:
                task_summary += f"- [{t['id']}] {t['title']}\n"

    content = f"{memory}{task_summary}"

    if output_path is None:
        output_path = os.path.join(BASE_DIR, ".conway", "mobile_export.md")

    with open(output_path, "w") as f:
        f.write(content)

    return True, output_path

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "pull":
        ok, msg = pull()
        print(f"{'✅' if ok else '❌'} {msg}")

    elif cmd == "push":
        ok, msg = push()
        print(f"{'✅' if ok else '❌'} {msg}")

    elif cmd == "export":
        ok, result = export_for_mobile()
        if ok:
            print(f"✅ 모바일 내보내기 완료: {result}")
            print("→ Claude Projects에 이 파일을 업로드하거나 내용을 복사해 사용하세요.")
        else:
            print(f"❌ {result}")

    elif cmd == "status":
        changed = memory_changed()
        print(f"memory.md 변경: {'있음 (미동기화)' if changed else '없음 (최신)'}")

    else:
        print("사용법:")
        print("  python conway/sync.py pull    원격에서 최신 memory.md 가져오기")
        print("  python conway/sync.py push    로컬 변경사항 원격에 푸시")
        print("  python conway/sync.py export  모바일/Projects용 파일 생성")
        print("  python conway/sync.py status  동기화 상태 확인")

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    main()
