# -*- coding: utf-8 -*-
"""
치매간병보험 DM 발송 보조 — 카카오톡 반자동화 도구

월 50명 이관 고객 대상 7일 시퀀스 카카오톡 발송을 보조한다.
  - 오늘 발송할 고객 자동 계산
  - 카드 이미지 열기 / 메시지 문안 클립보드 복사
  - 발송 완료 체크 및 로그 기록

실행:
  python sender_app.py   (또는 발송보조.bat 더블클릭)

cards/ 폴더에 day1.png ~ day7.png 카드 이미지를 넣어두면 자동 인식.
"""

import csv
import json
import os
import subprocess
import sys
import tkinter as tk
import uuid
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import broadcast_messages as bm

BASE           = Path(__file__).parent
CARDS_DIR      = BASE / "cards"
DATA_FILE      = BASE / "customers.json"
LOG_FILE       = BASE / "send_log.json"
BROADCAST_LOG  = BASE / "broadcast_log.json"
BROADCAST_CFG  = BASE / "broadcast_cfg.json"

NAVY  = "#1f3a5f"
CORAL = "#e8533f"
GRAY  = "#f4f7fb"

AGENT_TITLE = "롯데손해보험 전속설계사"
AGENT_NAME  = "권용준"
AGENT_TEL   = "010-6783-2588"
OPTOUT_TEL  = "080-870-5377"

# ── 7일 메시지 템플릿 ──────────────────────────────────────────────────────────
DAYS = {
    1: dict(
        label="안부",
        has_image=True,
        is_ad=False,
        text=(
            "{cname} 고객님, 벌써 여름 날씨네요. 더위에 건강 잘 챙기고 계신가요?\n"
            "수분 자주 드시고, 한낮 무더위엔 잠시 쉬어가세요. 오늘도 평안한 하루 되세요. 🥤"
        ),
    ),
    2: dict(
        label="치매 현실",
        has_image=True,
        is_ad=False,
        text=(
            "요즘 치매가 정말 남의 일이 아니더라고요.\n"
            "자녀 10명 중 6명이 부모님 치매를 걱정한다는 조사도 있어요.\n"
            "한 번 편하게 읽어보시라고 공유드려요."
        ),
    ),
    3: dict(
        label="간병 비용",
        has_image=True,
        is_ad=False,
        text=(
            "치매는 '긴 간병'이 핵심이라 비용이 만만치 않아요.\n"
            "1인당 연간 관리비용이 약 2,639만 원, 장기요양보험을 써도 본인부담 20%는 남습니다.\n"
            "걱정은 65.5%인데 실제 대비는 22.4%뿐이래요."
        ),
    ),
    4: dict(
        label="치료비",
        has_image=True,
        is_ad=False,
        text=(
            "요즘 '레켐비'라는 치매 신약이 화제예요.\n"
            "진행을 늦춰주지만 18개월에 약 6,480만 원, 대부분 비급여라 부담이 커요.\n"
            "치료를 받고 싶어도 준비가 안 되면 포기하게 되는 게 현실이더라고요."
        ),
    ),
    5: dict(
        label="보험 점검",
        has_image=True,
        is_ad=True,
        text=(
            "(광고) {cname} 고객님, 지금 가입하신 치매보험 한 가지만 확인해보세요.\n"
            "'갱신형'이면 납입면제돼도 갱신 후 다시 납입이 시작되고,\n"
            "환급금 노려 65세에 해지하면 정작 위험한 시기에 보장이 사라져요.\n"
            "\n무료수신거부 " + OPTOUT_TEL
        ),
    ),
    6: dict(
        label="해결책",
        has_image=True,
        is_ad=True,
        text=(
            "(광고) 그래서 요즘은 '해지해서 받는 환급금' 컨셉 대신,\n"
            "비갱신형 + 전기간(100세) 납입면제로 가는 분들이 많아요.\n"
            "검사·진단·치료·입원·통원까지 단계별로 보장됩니다.\n"
            "\n무료수신거부 " + OPTOUT_TEL
        ),
    ),
    7: dict(
        label="무료 점검",
        has_image=True,
        is_ad=True,
        text=(
            "(광고) 일주일간 보내드린 정보, 도움이 되셨길 바라요.\n"
            "지금 보험으로 충분한지 '점검'만 무료로 도와드릴게요. 가입 권유 아니에요.\n"
            "필요하실 때 편히 말씀 주세요.\n"
            "— {title} {aname} {tel}\n"
            "\n무료수신거부 " + OPTOUT_TEL
        ),
    ),
}


def build_message(day: int, cname: str) -> str:
    return DAYS[day]["text"].format(
        cname=cname,
        title=AGENT_TITLE,
        aname=AGENT_NAME,
        tel=AGENT_TEL,
    )


def card_image(day: int):
    for ext in ("png", "jpg", "jpeg"):
        p = CARDS_DIR / f"day{day}.{ext}"
        if p.exists():
            return p
    return None


def open_file(path: Path):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


# ── 데이터 ──────────────────────────────────────────────────────────────────

def load_customers():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def save_customers(customers):
    DATA_FILE.write_text(
        json.dumps(customers, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return []


def save_log(log):
    LOG_FILE.write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def is_sent(log, cid: str, day: int) -> bool:
    return any(e["cid"] == cid and e["day"] == day for e in log)


def mark_sent(log, cid: str, day: int):
    log.append({"cid": cid, "day": day, "date": date.today().isoformat()})
    return log


def today_targets(customers, log):
    today = date.today()
    result = []
    for c in customers:
        start = date.fromisoformat(c["start_date"])
        day_num = (today - start).days + 1
        if 1 <= day_num <= 7 and not is_sent(log, c["id"], day_num):
            result.append({"customer": c, "day": day_num})
    return result


# ── GUI ─────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("치매간병보험 DM 발송 보조")
        self.geometry("900x640")
        self.configure(bg=GRAY)
        self.resizable(True, True)

        self.customers = load_customers()
        self.log = load_log()

        self._build_header()
        self._build_tabs()
        self.refresh()

    # ── 헤더 ──

    def _build_header(self):
        hdr = tk.Frame(self, bg=NAVY, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="치매간병보험 DM 발송 보조",
            bg=NAVY, fg="white", font=("맑은 고딕", 15, "bold"),
        ).pack(side="left", padx=20, pady=14)
        tk.Label(
            hdr, text=f"{AGENT_TITLE} {AGENT_NAME}  {AGENT_TEL}",
            bg=NAVY, fg="#a8c4e0", font=("맑은 고딕", 9),
        ).pack(side="right", padx=20)

    # ── 탭 ──

    def _build_tabs(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=12, pady=10)

        self.tab_today     = tk.Frame(self.nb, bg=GRAY)
        self.tab_broadcast = tk.Frame(self.nb, bg=GRAY)
        self.tab_customers = tk.Frame(self.nb, bg=GRAY)
        self.tab_status    = tk.Frame(self.nb, bg=GRAY)

        self.nb.add(self.tab_today,     text="  📤 7일 시퀀스  ")
        self.nb.add(self.tab_broadcast, text="  📢 주간 DM  ")
        self.nb.add(self.tab_customers, text="  👥 고객 관리  ")
        self.nb.add(self.tab_status,    text="  📊 전체 현황  ")

        self._build_today_tab()
        self._build_broadcast_tab()
        self._build_customers_tab()
        self._build_status_tab()

    # ── 오늘 발송 탭 ──────────────────────────────────────────────────────────

    def _build_today_tab(self):
        f = self.tab_today

        top = tk.Frame(f, bg=GRAY)
        top.pack(fill="x", padx=8, pady=(10, 4))
        self.lbl_today = tk.Label(
            top, text="", bg=GRAY, fg=NAVY, font=("맑은 고딕", 12, "bold")
        )
        self.lbl_today.pack(side="left")
        tk.Button(
            top, text="새로고침", bg="#dfe5ec", fg=NAVY,
            font=("맑은 고딕", 9), relief="flat", cursor="hand2",
            command=self.refresh,
        ).pack(side="right")

        canvas = tk.Canvas(f, bg=GRAY, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        self.today_inner = tk.Frame(canvas, bg=GRAY)
        self.today_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.today_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        sb.pack(side="right", fill="y", pady=4)

        # 마우스 휠 스크롤
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._today_canvas = canvas

    def _refresh_today(self):
        targets = today_targets(self.customers, self.log)
        today_str = date.today().strftime("%Y년 %m월 %d일")
        self.lbl_today.config(text=f"{today_str}  ·  발송 대상 {len(targets)}명")

        for w in self.today_inner.winfo_children():
            w.destroy()

        if not targets:
            tk.Label(
                self.today_inner,
                text="오늘 발송할 고객이 없습니다 😊",
                bg=GRAY, fg="#5f6c7b", font=("맑은 고딕", 12),
            ).pack(pady=60)
            return

        for item in targets:
            self._build_send_row(self.today_inner, item)

    def _build_send_row(self, parent, item: dict):
        c   = item["customer"]
        day = item["day"]
        info = DAYS[day]
        msg  = build_message(day, c["name"])
        img  = card_image(day)

        row = tk.Frame(parent, bg="white", highlightbackground="#dfe5ec",
                       highlightthickness=1)
        row.pack(fill="x", padx=4, pady=3, ipady=4)

        # 일차 배지
        badge_frame = tk.Frame(row, bg=CORAL, width=58)
        badge_frame.pack(side="left", fill="y")
        badge_frame.pack_propagate(False)
        tk.Label(
            badge_frame, text=f"{day}일차\n{info['label']}",
            bg=CORAL, fg="white", font=("맑은 고딕", 9, "bold"),
        ).pack(expand=True)

        # 이름
        name_frame = tk.Frame(row, bg="white", width=90)
        name_frame.pack(side="left", fill="y", padx=(10, 0))
        name_frame.pack_propagate(False)
        tk.Label(
            name_frame, text=c["name"],
            bg="white", fg=NAVY, font=("맑은 고딕", 12, "bold"),
        ).pack(expand=True)
        if info["is_ad"]:
            tk.Label(
                name_frame, text="⚠ 광고",
                bg="white", fg="#e67e22", font=("맑은 고딕", 8),
            ).pack()

        # 메시지 미리보기
        txt = tk.Text(
            row, height=3, font=("맑은 고딕", 9),
            bg="#f8f9fa", fg="#2b2b2b", relief="flat",
            wrap="word", state="normal", cursor="arrow",
        )
        txt.insert("1.0", msg)
        txt.config(state="disabled")
        txt.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        # 버튼 영역
        btn_frame = tk.Frame(row, bg="white", width=140)
        btn_frame.pack(side="right", padx=8, pady=6)
        btn_frame.pack_propagate(False)

        if img:
            tk.Button(
                btn_frame, text="🖼 이미지 열기",
                bg="#2b5f8f", fg="white",
                font=("맑은 고딕", 9, "bold"), relief="flat", cursor="hand2",
                command=lambda p=img: open_file(p),
            ).pack(fill="x", pady=2, ipady=3)

        tk.Button(
            btn_frame, text="📋 메시지 복사",
            bg=NAVY, fg="white",
            font=("맑은 고딕", 9, "bold"), relief="flat", cursor="hand2",
            command=lambda m=msg: self._copy(m),
        ).pack(fill="x", pady=2, ipady=3)

        done_btn = tk.Button(
            btn_frame, text="✓ 발송 완료",
            bg="#27ae60", fg="white",
            font=("맑은 고딕", 9, "bold"), relief="flat", cursor="hand2",
        )
        done_btn.pack(fill="x", pady=2, ipady=3)
        done_btn.config(
            command=lambda cid=c["id"], d=day, r=row, b=done_btn:
                self._mark_done(cid, d, r, b)
        )

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _mark_done(self, cid: str, day: int, row: tk.Frame, btn: tk.Button):
        self.log = mark_sent(self.log, cid, day)
        save_log(self.log)
        btn.config(state="disabled", text="✓ 완료", bg="#95a5a6")
        row.configure(highlightbackground="#27ae60", highlightthickness=2)
        self._refresh_status()
        self._refresh_customers()

    # ── 주간 DM 브로드캐스트 탭 ──────────────────────────────────────────────

    def _load_broadcast_log(self):
        if BROADCAST_LOG.exists():
            return json.loads(BROADCAST_LOG.read_text(encoding="utf-8"))
        return []

    def _save_broadcast_log(self, log):
        BROADCAST_LOG.write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_broadcast_cfg(self):
        if BROADCAST_CFG.exists():
            return json.loads(BROADCAST_CFG.read_text(encoding="utf-8"))
        return {"campaign_start": date.today().isoformat()}

    def _save_broadcast_cfg(self, cfg):
        BROADCAST_CFG.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _auto_week(self):
        cfg = self._load_broadcast_cfg()
        start = date.fromisoformat(cfg.get("campaign_start", date.today().isoformat()))
        delta = (date.today() - start).days
        week = min(8, max(1, delta // 7 + 1))
        return week

    def _build_broadcast_tab(self):
        f = self.tab_broadcast
        self._bc_log = self._load_broadcast_log()

        # ── 상단 컨트롤 ──
        ctrl = tk.Frame(f, bg=GRAY)
        ctrl.pack(fill="x", padx=10, pady=(10, 4))

        tk.Label(ctrl, text="주차", bg=GRAY, fg=NAVY,
                 font=("맑은 고딕", 11, "bold")).pack(side="left")
        self._bc_week = tk.IntVar(value=self._auto_week())
        tk.Spinbox(ctrl, from_=1, to=8, textvariable=self._bc_week,
                   width=3, font=("맑은 고딕", 12, "bold"),
                   command=self._refresh_broadcast).pack(side="left", padx=(4, 14))

        tk.Label(ctrl, text="요일", bg=GRAY, fg=NAVY,
                 font=("맑은 고딕", 11, "bold")).pack(side="left")
        self._bc_day = tk.StringVar(value="화")
        for d in ("화", "금"):
            tk.Radiobutton(
                ctrl, text=d, variable=self._bc_day, value=d,
                bg=GRAY, fg=NAVY, font=("맑은 고딕", 11, "bold"),
                activebackground=GRAY, selectcolor="#dfe5ec",
                command=self._refresh_broadcast,
            ).pack(side="left", padx=4)

        tk.Button(
            ctrl, text="캠페인 시작일 설정", bg="#dfe5ec", fg=NAVY,
            font=("맑은 고딕", 9), relief="flat", cursor="hand2",
            command=self._set_campaign_start,
        ).pack(side="right")

        # ── 메시지 미리보기 ──
        preview_frame = tk.Frame(f, bg="white", highlightbackground="#dfe5ec",
                                  highlightthickness=1)
        preview_frame.pack(fill="x", padx=10, pady=4)

        self._bc_topic_lbl = tk.Label(
            preview_frame, text="", bg=CORAL, fg="white",
            font=("맑은 고딕", 10, "bold"), anchor="w", padx=8, pady=4,
        )
        self._bc_topic_lbl.pack(fill="x")

        self._bc_preview = tk.Text(
            preview_frame, height=7, font=("맑은 고딕", 9),
            bg="#f8f9fa", fg="#2b2b2b", relief="flat", wrap="word",
        )
        self._bc_preview.pack(fill="x", padx=8, pady=6)

        # ── 고객 목록 ──
        list_hdr = tk.Frame(f, bg=GRAY)
        list_hdr.pack(fill="x", padx=10, pady=(6, 2))
        self._bc_count_lbl = tk.Label(
            list_hdr, text="", bg=GRAY, fg=NAVY, font=("맑은 고딕", 10, "bold")
        )
        self._bc_count_lbl.pack(side="left")
        tk.Button(
            list_hdr, text="📋 전체 문안 복사 (첫 번째 고객)", bg="#2b5f8f", fg="white",
            font=("맑은 고딕", 9), relief="flat", cursor="hand2",
            command=self._copy_broadcast_sample,
        ).pack(side="right")

        canvas = tk.Canvas(f, bg=GRAY, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        self._bc_inner = tk.Frame(canvas, bg=GRAY)
        self._bc_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._bc_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=4)
        sb.pack(side="right", fill="y", pady=4)
        self._bc_canvas = canvas

        self._refresh_broadcast()

    def _refresh_broadcast(self):
        week = self._bc_week.get()
        day  = self._bc_day.get()

        topic = bm.get_topic(week, day)
        ad    = bm.is_ad(week, day)
        sample_msg = bm.get_message(week, day, "고객님")

        self._bc_topic_lbl.config(
            text=f"  {week}주차 {day}요일  ·  {topic}"
                 + ("  ⚠ 광고" if ad else ""),
            bg=CORAL if not ad else "#c0392b",
        )
        self._bc_preview.config(state="normal")
        self._bc_preview.delete("1.0", "end")
        self._bc_preview.insert("1.0", sample_msg)
        self._bc_preview.config(state="disabled")

        for w in self._bc_inner.winfo_children():
            w.destroy()

        sent_ids = {
            e["cid"] for e in self._bc_log
            if e["week"] == week and e["day"] == day
        }
        pending = [c for c in self.customers if c["id"] not in sent_ids]
        done    = [c for c in self.customers if c["id"] in sent_ids]

        self._bc_count_lbl.config(
            text=f"전체 {len(self.customers)}명  |  미발송 {len(pending)}명  |  완료 {len(done)}명"
        )

        for c in pending:
            self._build_bc_row(self._bc_inner, c, week, day, sent=False)
        for c in done:
            self._build_bc_row(self._bc_inner, c, week, day, sent=True)

    def _build_bc_row(self, parent, c, week, day, sent=False):
        bg_color = "#f0faf0" if sent else "white"
        row = tk.Frame(parent, bg=bg_color, highlightbackground="#dfe5ec",
                       highlightthickness=1)
        row.pack(fill="x", padx=2, pady=2, ipady=3)

        tk.Label(row, text=c["name"], bg=bg_color, fg=NAVY,
                 font=("맑은 고딕", 11, "bold"), width=8).pack(side="left", padx=12)
        tk.Label(row, text=c.get("phone", ""), bg=bg_color, fg="#5f6c7b",
                 font=("맑은 고딕", 9), width=14).pack(side="left")

        if sent:
            tk.Label(row, text="✅ 발송 완료", bg=bg_color, fg="#27ae60",
                     font=("맑은 고딕", 9, "bold")).pack(side="right", padx=12)
        else:
            done_btn = tk.Button(
                row, text="✓ 완료", bg="#27ae60", fg="white",
                font=("맑은 고딕", 9, "bold"), relief="flat", cursor="hand2",
                width=6,
            )
            done_btn.pack(side="right", padx=4, ipady=2)
            done_btn.config(
                command=lambda cid=c["id"], w=week, d=day, r=row, b=done_btn:
                    self._bc_mark_done(cid, w, d, r, b)
            )
            tk.Button(
                row, text="📋 복사", bg=NAVY, fg="white",
                font=("맑은 고딕", 9, "bold"), relief="flat", cursor="hand2",
                width=6,
                command=lambda name=c["name"]: self._copy(bm.get_message(week, day, name)),
            ).pack(side="right", padx=4, ipady=2)

    def _bc_mark_done(self, cid, week, day, row, btn):
        self._bc_log.append({
            "cid": cid, "week": week, "day": day,
            "date": date.today().isoformat(),
        })
        self._save_broadcast_log(self._bc_log)
        btn.config(state="disabled", text="✅", bg="#95a5a6")
        row.configure(bg="#f0faf0", highlightbackground="#27ae60")
        self._bc_count_lbl.config(
            text=self._bc_count_lbl.cget("text")  # 즉각 리프레시 없이 색만 변경
        )

    def _copy_broadcast_sample(self):
        if self.customers:
            self._copy(bm.get_message(
                self._bc_week.get(), self._bc_day.get(),
                self.customers[0]["name"]
            ))

    def _set_campaign_start(self):
        dlg = tk.Toplevel(self)
        dlg.title("캠페인 시작일")
        dlg.geometry("300x140")
        dlg.configure(bg=GRAY)
        dlg.transient(self)
        dlg.grab_set()

        cfg = self._load_broadcast_cfg()
        tk.Label(dlg, text="캠페인 시작일 (1주차 화요일)",
                 bg=GRAY, fg=NAVY, font=("맑은 고딕", 10)).pack(padx=16, pady=10)
        var = tk.StringVar(value=cfg.get("campaign_start", date.today().isoformat()))
        tk.Entry(dlg, textvariable=var, font=("맑은 고딕", 11), width=16).pack()

        def save():
            try:
                date.fromisoformat(var.get().strip())
                cfg["campaign_start"] = var.get().strip()
                self._save_broadcast_cfg(cfg)
                self._bc_week.set(self._auto_week())
                self._refresh_broadcast()
                dlg.destroy()
            except ValueError:
                messagebox.showwarning("형식 오류", "YYYY-MM-DD 형식으로 입력하세요.", parent=dlg)

        tk.Button(dlg, text="저장", bg=CORAL, fg="white",
                  font=("맑은 고딕", 11, "bold"), relief="flat",
                  command=save).pack(pady=12, ipadx=20, ipady=4)

    # ── 고객 관리 탭 ──────────────────────────────────────────────────────────

    def _build_customers_tab(self):
        f = self.tab_customers

        toolbar = tk.Frame(f, bg=GRAY)
        toolbar.pack(fill="x", padx=8, pady=(10, 4))

        for text, bg, cmd in [
            ("+ 고객 추가",    CORAL,    self._add_customer),
            ("📥 CSV 가져오기", "#2b5f8f", self._import_csv),
            ("🗑 선택 삭제",   "#c0392b", self._delete_customer),
        ]:
            tk.Button(
                toolbar, text=text, bg=bg, fg="white",
                font=("맑은 고딕", 10, "bold"), relief="flat",
                cursor="hand2", command=cmd,
            ).pack(side="left", ipady=5, padx=(0, 6))

        tk.Label(
            toolbar,
            text="CSV 형식: 이름, 전화번호, 시작일  (헤더 행 필요)",
            bg=GRAY, fg="#5f6c7b", font=("맑은 고딕", 8),
        ).pack(side="right", padx=4)

        cols = ("name", "phone", "start_date", "progress")
        self.cust_tree = ttk.Treeview(f, columns=cols, show="headings", selectmode="browse")
        for col, hdr, w in [
            ("name",       "이름",   100),
            ("phone",      "전화번호", 130),
            ("start_date", "시작일",  110),
            ("progress",   "진행 상황", 280),
        ]:
            self.cust_tree.heading(col, text=hdr)
            self.cust_tree.column(col, width=w, anchor="center")

        sb2 = ttk.Scrollbar(f, orient="vertical", command=self.cust_tree.yview)
        self.cust_tree.configure(yscrollcommand=sb2.set)
        self.cust_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb2.pack(side="right", fill="y", pady=4, padx=(0, 8))

    def _refresh_customers(self):
        self.cust_tree.delete(*self.cust_tree.get_children())
        today = date.today()
        for c in self.customers:
            start   = date.fromisoformat(c["start_date"])
            day_num = (today - start).days + 1
            sent    = [e["day"] for e in self.log if e["cid"] == c["id"]]
            done    = len(sent)
            if day_num < 1:
                progress = f"대기 중 ({(start - today).days}일 후 시작)"
            elif day_num > 7:
                progress = f"✅ 완료 ({done}/7 발송)"
            else:
                progress = f"{day_num}일차 진행 중  ({done}/7 발송 완료)"
            self.cust_tree.insert(
                "", "end", iid=c["id"],
                values=(c["name"], c.get("phone", ""), c["start_date"], progress),
            )

    def _add_customer(self):
        dlg = tk.Toplevel(self)
        dlg.title("고객 추가")
        dlg.geometry("340x230")
        dlg.configure(bg=GRAY)
        dlg.transient(self)
        dlg.grab_set()

        fields = {}
        for i, (label, key, default) in enumerate([
            ("이름",              "name",       ""),
            ("전화번호",           "phone",      ""),
            ("시작일 (YYYY-MM-DD)", "start_date", date.today().isoformat()),
        ]):
            tk.Label(dlg, text=label, bg=GRAY, fg=NAVY,
                     font=("맑은 고딕", 10)).grid(row=i, column=0, padx=16, pady=8, sticky="w")
            var = tk.StringVar(value=default)
            tk.Entry(dlg, textvariable=var, font=("맑은 고딕", 10), width=22).grid(
                row=i, column=1, padx=8, pady=8,
            )
            fields[key] = var

        def save():
            name  = fields["name"].get().strip()
            phone = fields["phone"].get().strip()
            start = fields["start_date"].get().strip()
            if not name:
                messagebox.showwarning("입력 필요", "이름을 입력하세요.", parent=dlg)
                return
            try:
                date.fromisoformat(start)
            except ValueError:
                messagebox.showwarning("형식 오류", "시작일을 YYYY-MM-DD 형식으로 입력하세요.", parent=dlg)
                return
            self.customers.append({
                "id":         str(uuid.uuid4())[:8],
                "name":       name,
                "phone":      phone,
                "start_date": start,
            })
            save_customers(self.customers)
            self.refresh()
            dlg.destroy()

        tk.Button(
            dlg, text="저장", bg=CORAL, fg="white",
            font=("맑은 고딕", 11, "bold"), relief="flat", command=save,
        ).grid(row=3, column=0, columnspan=2, pady=14, ipadx=24, ipady=5)

    def _import_csv(self):
        path = filedialog.askopenfilename(
            title="고객 CSV 열기",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        added = 0
        try:
            with open(path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name  = row.get("이름", "").strip()
                    phone = row.get("전화번호", "").strip()
                    start = row.get("시작일", date.today().isoformat()).strip()
                    if not name:
                        continue
                    try:
                        date.fromisoformat(start)
                    except ValueError:
                        start = date.today().isoformat()
                    self.customers.append({
                        "id":         str(uuid.uuid4())[:8],
                        "name":       name,
                        "phone":      phone,
                        "start_date": start,
                    })
                    added += 1
            save_customers(self.customers)
            self.refresh()
            messagebox.showinfo("가져오기 완료", f"{added}명이 추가됐습니다.")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def _delete_customer(self):
        sel = self.cust_tree.selection()
        if not sel:
            return
        cid = sel[0]
        c   = next((x for x in self.customers if x["id"] == cid), None)
        if not c:
            return
        if messagebox.askyesno(
            "삭제 확인",
            f"'{c['name']}' 고객을 삭제할까요?\n발송 로그도 함께 삭제됩니다.",
        ):
            self.customers = [x for x in self.customers if x["id"] != cid]
            self.log       = [e for e in self.log if e["cid"] != cid]
            save_customers(self.customers)
            save_log(self.log)
            self.refresh()

    # ── 전체 현황 탭 ──────────────────────────────────────────────────────────

    def _build_status_tab(self):
        f = self.tab_status

        top = tk.Frame(f, bg=GRAY)
        top.pack(fill="x", padx=8, pady=(10, 4))
        self.lbl_status = tk.Label(
            top, text="", bg=GRAY, fg=NAVY, font=("맑은 고딕", 11, "bold")
        )
        self.lbl_status.pack(side="left")

        cols = ("name",) + tuple(str(d) for d in range(1, 8))
        self.status_tree = ttk.Treeview(f, columns=cols, show="headings")
        self.status_tree.heading("name", text="이름")
        self.status_tree.column("name", width=100, anchor="center")
        for d in range(1, 8):
            label = f"{d}일 {DAYS[d]['label']}"
            self.status_tree.heading(str(d), text=label)
            self.status_tree.column(str(d), width=90, anchor="center")

        sb3 = ttk.Scrollbar(f, orient="vertical", command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=sb3.set)
        self.status_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb3.pack(side="right", fill="y", pady=4, padx=(0, 8))

    def _refresh_status(self):
        today = date.today()
        total = len(self.customers)
        done_count = sum(
            1 for c in self.customers
            if len([e for e in self.log if e["cid"] == c["id"]]) == 7
        )
        active = sum(
            1 for c in self.customers
            if 1 <= (today - date.fromisoformat(c["start_date"])).days + 1 <= 7
        )
        self.lbl_status.config(
            text=f"전체 {total}명  |  진행중 {active}명  |  완료 {done_count}명"
        )

        self.status_tree.delete(*self.status_tree.get_children())
        for c in self.customers:
            sent    = {e["day"] for e in self.log if e["cid"] == c["id"]}
            start   = date.fromisoformat(c["start_date"])
            cur_day = (today - start).days + 1
            vals    = [c["name"]]
            for d in range(1, 8):
                if d in sent:
                    vals.append("✅")
                elif d == cur_day:
                    vals.append("▶ 오늘")
                elif d < cur_day:
                    vals.append("❌ 미발송")
                else:
                    vals.append("·")
            self.status_tree.insert("", "end", values=vals)

    # ── 공통 ──

    def refresh(self):
        self._refresh_today()
        self._refresh_broadcast()
        self._refresh_customers()
        self._refresh_status()


def main():
    CARDS_DIR.mkdir(exist_ok=True)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
