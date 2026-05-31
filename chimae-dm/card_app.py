# -*- coding: utf-8 -*-
"""
치매간병보험 카드 생성기 — 데스크톱 GUI

CMD 없이 버튼 클릭만으로 gpt-image-2 카드 7장을 생성한다.
  - API 키 붙여넣기 → [카드 생성] 버튼 → 진행상황 표시 → 완료 시 폴더 자동 오픈

실행:
  python card_app.py          (또는 run_gui.bat 더블클릭)

필요 패키지: openai, pillow  (tkinter 는 파이썬 기본 포함)
"""
import os
import sys
import threading
import subprocess
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

BASE = Path(__file__).parent
OUT = BASE / "out_gpt"
KEY_FILE = BASE / ".openai_key"   # 로컬 저장 (gitignore 처리됨, 절대 커밋 안 됨)


def load_key() -> str:
    """저장된 키 불러오기 (없으면 빈 문자열)."""
    try:
        if KEY_FILE.exists():
            return KEY_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY", "")


def save_key(key: str):
    """키를 로컬 파일에 저장 (다음 실행 시 자동 입력)."""
    try:
        KEY_FILE.write_text(key.strip(), encoding="utf-8")
    except Exception:
        pass


def _ensure_deps(log):
    """openai 패키지가 없으면 설치."""
    try:
        import openai  # noqa
        return True
    except ImportError:
        log("📦 openai 패키지 설치 중... (최초 1회)")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", "openai", "pillow"]
            )
            log("✅ 설치 완료")
            return True
        except Exception as e:
            log(f"❌ 설치 실패: {e}")
            return False


def _generate(api_key, quality, log, on_done):
    """백그라운드 스레드에서 카드 생성."""
    try:
        if not _ensure_deps(log):
            on_done(False)
            return

        os.environ["OPENAI_API_KEY"] = api_key.strip()
        from openai import OpenAI
        import card  # 그라운딩된 7일 콘텐츠
        import base64

        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        OUT.mkdir(exist_ok=True)
        client = OpenAI()
        specs = card.card_specs()

        # gpt_image.py 의 프롬프트 빌더 재사용
        import gpt_image

        log(f"🎨 gpt-image-2 로 {len(specs)}장 '동시' 생성 시작 (품질: {quality})")
        log("   (한 장씩이 아니라 동시에 요청 → 훨씬 빠름)")
        t0 = time.time()

        def _one(s):
            resp = client.images.generate(
                model="gpt-image-2",
                prompt=gpt_image.build_prompt(s),
                size="1024x1536",
                quality=quality,
            )
            (OUT / f"gptcard_day{s['day']}.png").write_bytes(
                base64.b64decode(resp.data[0].b64_json)
            )
            return s["day"]

        done = 0
        with ThreadPoolExecutor(max_workers=len(specs)) as ex:
            futures = [ex.submit(_one, s) for s in specs]
            for fut in as_completed(futures):
                day = fut.result()
                done += 1
                log(f"   ✅ {day}일차 완료  ({done}/{len(specs)}, {time.time()-t0:.0f}초)")

        log("")
        log(f"🎉 완료! 총 {len(specs)}장 · {time.time()-t0:.0f}초 → {OUT}")
        on_done(True)
    except Exception as e:
        log("")
        log(f"❌ 오류: {e}")
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg or "Incorrect API key" in msg:
            log("   → API 키가 잘못되었습니다. 키를 다시 확인하세요.")
        elif "403" in msg or "allowlist" in msg:
            log("   → 네트워크가 api.openai.com 접속을 차단하고 있습니다.")
        elif "insufficient_quota" in msg or "billing" in msg:
            log("   → OpenAI 결제/잔액을 확인하세요.")
        on_done(False)


def open_folder():
    OUT.mkdir(exist_ok=True)
    if sys.platform == "win32":
        os.startfile(OUT)  # type: ignore
    elif sys.platform == "darwin":
        subprocess.run(["open", str(OUT)])
    else:
        subprocess.run(["xdg-open", str(OUT)])


def main():
    root = tk.Tk()
    root.title("치매간병보험 카드 생성기 — gpt-image-2")
    root.geometry("640x560")
    root.configure(bg="#f4f7fb")

    NAVY = "#1f3a5f"
    CORAL = "#e8533f"

    # ── 헤더 ──
    header = tk.Frame(root, bg=NAVY, height=70)
    header.pack(fill="x")
    tk.Label(
        header, text="치매간병보험 정보 카드 생성기",
        bg=NAVY, fg="white", font=("맑은 고딕", 16, "bold"),
    ).pack(pady=18)

    body = tk.Frame(root, bg="#f4f7fb", padx=24, pady=18)
    body.pack(fill="both", expand=True)

    # ── API 키 입력 ──
    tk.Label(
        body, text="OpenAI API 키", bg="#f4f7fb", fg=NAVY,
        font=("맑은 고딕", 11, "bold"),
    ).pack(anchor="w")
    tk.Label(
        body, text="platform.openai.com/api-keys 에서 발급 (sk-proj-... 로 시작)",
        bg="#f4f7fb", fg="#5f6c7b", font=("맑은 고딕", 9),
    ).pack(anchor="w")

    key_var = tk.StringVar(value=load_key())   # 저장된 키 자동 입력
    key_entry = tk.Entry(body, textvariable=key_var, show="•",
                         font=("Consolas", 11), width=60)
    key_entry.pack(fill="x", pady=(4, 4), ipady=5)

    optrow = tk.Frame(body, bg="#f4f7fb")
    optrow.pack(anchor="w", fill="x")

    show_var = tk.BooleanVar(value=False)

    def toggle_show():
        key_entry.config(show="" if show_var.get() else "•")

    tk.Checkbutton(
        optrow, text="키 보이기", variable=show_var, command=toggle_show,
        bg="#f4f7fb", fg="#5f6c7b", font=("맑은 고딕", 9),
        activebackground="#f4f7fb", selectcolor="#f4f7fb",
    ).pack(side="left")

    remember_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        optrow, text="이 PC에 키 저장 (다음부터 자동 입력)", variable=remember_var,
        bg="#f4f7fb", fg="#5f6c7b", font=("맑은 고딕", 9),
        activebackground="#f4f7fb", selectcolor="#f4f7fb",
    ).pack(side="left", padx=10)

    if load_key():
        key_entry.config(show="•")

    # ── 품질 선택 ──
    qframe = tk.Frame(body, bg="#f4f7fb")
    qframe.pack(fill="x", pady=(8, 4))
    tk.Label(
        qframe, text="품질:", bg="#f4f7fb", fg=NAVY,
        font=("맑은 고딕", 11, "bold"),
    ).pack(side="left")
    quality_var = tk.StringVar(value="high")
    for txt, val, price in [
        ("저화질 (장당 ~8원)", "low", ""),
        ("표준 (장당 ~70원)", "medium", ""),
        ("고화질 (장당 ~290원, 추천)", "high", ""),
    ]:
        tk.Radiobutton(
            qframe, text=txt, variable=quality_var, value=val,
            bg="#f4f7fb", fg="#23303f", font=("맑은 고딕", 9),
            activebackground="#f4f7fb", selectcolor="#dfe5ec",
        ).pack(side="left", padx=4)

    # ── 로그 출력 ──
    log_box = tk.Text(body, height=12, font=("Consolas", 9),
                      bg="#1f2733", fg="#d8e0ea", relief="flat")
    log_box.pack(fill="both", expand=True, pady=(10, 8))

    def log(msg):
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        root.update_idletasks()

    # ── 버튼 ──
    btn_frame = tk.Frame(body, bg="#f4f7fb")
    btn_frame.pack(fill="x")

    gen_btn = tk.Button(
        btn_frame, text="🎨 카드 7장 생성", bg=CORAL, fg="white",
        font=("맑은 고딕", 12, "bold"), relief="flat", cursor="hand2",
        activebackground="#c8432f", activeforeground="white",
    )
    gen_btn.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 4))

    folder_btn = tk.Button(
        btn_frame, text="📂 결과 폴더", bg="#dfe5ec", fg=NAVY,
        font=("맑은 고딕", 11), relief="flat", cursor="hand2",
        command=open_folder,
    )
    folder_btn.pack(side="left", ipady=8, padx=(4, 0))

    def on_done(ok):
        gen_btn.config(state="normal", text="🎨 카드 7장 생성")
        if ok:
            open_folder()
            messagebox.showinfo("완료", "카드 7장이 생성되었습니다!\nout_gpt 폴더를 확인하세요.")

    def start():
        key = key_var.get().strip()
        if not key:
            messagebox.showwarning("키 필요", "OpenAI API 키를 입력하세요.")
            return
        if not key.startswith("sk-"):
            if not messagebox.askyesno("확인", "키 형식이 일반적이지 않습니다. 계속할까요?"):
                return
        if remember_var.get():
            save_key(key)        # 다음 실행부터 자동 입력
        gen_btn.config(state="disabled", text="생성 중...")
        log_box.delete("1.0", "end")
        threading.Thread(
            target=_generate,
            args=(key, quality_var.get(), log, on_done),
            daemon=True,
        ).start()

    gen_btn.config(command=start)

    if load_key():
        log("저장된 API 키를 불러왔습니다. [카드 7장 생성]을 누르세요.")
    else:
        log("준비 완료. API 키를 한 번만 붙여넣으면 다음부터 자동 입력됩니다.")
    root.mainloop()


if __name__ == "__main__":
    main()
