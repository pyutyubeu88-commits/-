"""
역삼효태권도장 컨설팅 보고서 PPT
Design System
─────────────────────────────────────────────────────
Background   : #F5F7FA  (모든 슬라이드)
Primary      : #0D1B3E  (네이비 – 제목, 헤더, 다크 요소)
Accent Red   : #C8102E  (레드 – 섹션 번호, 핵심 강조, 포인트)
White        : #FFFFFF  (카드 배경)
Border       : #DDE5F0  (카드 테두리)
Text Dark    : #1E2A3A
Text Mid     : #546E7A
Text Light   : #90A4AE
Green        : #1E8449  (완료/성과 표시)
─────────────────────────────────────────────────────
Rules
• 카드: 흰 배경 + 1px 테두리 + 왼쪽 3px 레드 액센트 바 (일관 적용)
• 제목: 항상 네이비 bold
• 색상 강조: 레드 한 가지만 핵심 요소에 사용
• 타이포 스케일 고정: 32pt(슬라이드 제목) / 14pt(소제목) / 11pt(본문) / 9pt(캡션)
• 슬라이드 상단: 3px 레드 full-width 선 + 네이비 헤더 밴드
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Design Tokens ──────────────────────────────────────────────────────────────
NAV   = RGBColor(0x0D, 0x1B, 0x3E)   # Navy
RED   = RGBColor(0xC8, 0x10, 0x2E)   # Accent Red
WHT   = RGBColor(0xFF, 0xFF, 0xFF)
BG    = RGBColor(0xF5, 0xF7, 0xFA)   # Slide background
BDR   = RGBColor(0xDD, 0xE5, 0xF0)   # Border
TXD   = RGBColor(0x1E, 0x2A, 0x3A)   # Text Dark
TXM   = RGBColor(0x54, 0x6E, 0x7A)   # Text Mid
TXL   = RGBColor(0x90, 0xA4, 0xAE)   # Text Light
GRN   = RGBColor(0x1E, 0x84, 0x49)   # Green (done)
NAV_LT= RGBColor(0x1A, 0x30, 0x5C)   # Lighter navy for cards on dark bg
RED_BG= RGBColor(0xFF, 0xF0, 0xF2)   # Light red tint
GRN_BG= RGBColor(0xF0, 0xFF, 0xF4)   # Light green tint

W = Inches(13.33)
H = Inches(7.5)
MARGIN = Inches(0.55)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]

# ── Primitives ─────────────────────────────────────────────────────────────────

def sl():
    return prs.slides.add_slide(BLANK)

def rect(slide, l, t, w, h, fill=None, line=None, lw=Pt(0.75)):
    s = slide.shapes.add_shape(1, l, t, w, h)
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = line; s.line.width = lw
    else:
        s.line.fill.background()
    return s

def oval(slide, l, t, w, h, fill):
    s = slide.shapes.add_shape(9, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.fill.background()
    return s

def txt(slide, text, l, t, w, h,
        size=11, bold=False, color=TXD, align=PP_ALIGN.LEFT, italic=False):
    b = slide.shapes.add_textbox(l, t, w, h)
    tf = b.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.italic = italic
    return b

def txt_in_rect(slide, text, l, t, w, h,
                size=11, bold=False, color=TXD,
                align=PP_ALIGN.LEFT, fill=None, line=None, lw=Pt(0.75)):
    r = rect(slide, l, t, w, h, fill=fill, line=line, lw=lw)
    tf = r.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    run = p.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = bold
    run.font.color.rgb = color
    return r

# ── Reusable Layout Blocks ─────────────────────────────────────────────────────

def bg(slide):
    rect(slide, 0, 0, W, H, fill=BG)

def slide_header(slide, section_num, title, subtitle=None):
    """Standard slide header: navy band + red top line."""
    BAND_H = Inches(1.25)
    rect(slide, 0, 0, W, Inches(0.04), fill=RED)           # top red rule
    rect(slide, 0, Inches(0.04), W, BAND_H, fill=NAV)       # navy band
    # section pill
    txt_in_rect(slide, section_num,
                MARGIN, Inches(0.32), Inches(0.52), Inches(0.52),
                size=12, bold=True, color=WHT,
                fill=RED, align=PP_ALIGN.CENTER)
    # title
    txt(slide, title,
        MARGIN + Inches(0.66), Inches(0.26), W - MARGIN * 2, Inches(0.62),
        size=26, bold=True, color=WHT)
    if subtitle:
        txt(slide, subtitle,
            MARGIN + Inches(0.66), Inches(0.84), W - MARGIN * 2, Inches(0.32),
            size=10, color=RGBColor(0x8A, 0xA4, 0xCC), italic=True)

def slide_footer(slide, page_n):
    FH = Inches(0.32)
    rect(slide, 0, H - FH, W, FH, fill=NAV)
    txt(slide, "역삼효태권도장  |  온라인 마케팅 컨설팅 보고서  |  2026.05",
        MARGIN, H - FH + Inches(0.05), Inches(8), FH,
        size=8, color=RGBColor(0x60, 0x7A, 0xA8))
    txt(slide, str(page_n),
        W - Inches(0.55), H - FH + Inches(0.05), Inches(0.4), FH,
        size=8, color=RGBColor(0x60, 0x7A, 0xA8), align=PP_ALIGN.RIGHT)

def card(slide, l, t, w, h, accent_color=RED):
    """White card with red left accent bar."""
    rect(slide, l, t, w, h, fill=WHT, line=BDR, lw=Pt(0.75))
    rect(slide, l, t, Inches(0.055), h, fill=accent_color)

def divider(slide, l, t, w):
    rect(slide, l, t, w, Inches(0.018), fill=BDR)

def label_tag(slide, text, l, t, w=Inches(1.5)):
    """Small uppercase label tag in red."""
    txt(slide, text.upper(), l, t, w, Inches(0.22),
        size=8, bold=True, color=RED)

def bullet_row(slide, text, l, t, w, bullet_color=RED, size=11):
    """Bullet row with colored square bullet."""
    rect(slide, l, t + Inches(0.07), Inches(0.06), Inches(0.06), fill=bullet_color)
    txt(slide, text, l + Inches(0.13), t, w - Inches(0.13), Inches(0.35),
        size=size, color=TXD)

def section_opener(slide, num, title, subtitle=""):
    """Dark full-bleed section transition slide."""
    rect(slide, 0, 0, W, H, fill=NAV)
    rect(slide, 0, 0, Inches(0.08), H, fill=RED)
    oval(slide, W - Inches(5), H / 2 - Inches(2.5), Inches(5), Inches(5),
         RGBColor(0x12, 0x26, 0x4E))
    txt(slide, num, MARGIN, Inches(2.0), Inches(2), Inches(0.65),
        size=13, bold=True, color=RED)
    rect(slide, MARGIN, Inches(2.62), Inches(0.85), Inches(0.05), fill=RED)
    txt(slide, title, MARGIN, Inches(2.75), Inches(9), Inches(1.4),
        size=52, bold=True, color=WHT)
    if subtitle:
        txt(slide, subtitle, MARGIN, Inches(4.25), Inches(9), Inches(0.5),
            size=16, color=RGBColor(0x8A, 0xA4, 0xCC), italic=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S01 — COVER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
rect(s, 0, 0, W, H, fill=NAV)
# subtle geometric accents
oval(s, W - Inches(4.8), Inches(-1.5), Inches(6), Inches(6),
     RGBColor(0x12, 0x26, 0x4E))
oval(s, W - Inches(2.2), H - Inches(3.0), Inches(4), Inches(4),
     RGBColor(0x0A, 0x14, 0x2C))
rect(s, 0, 0, Inches(0.08), H, fill=RED)
rect(s, 0, H - Inches(0.06), W, Inches(0.06), fill=RED)

# eyebrow label
txt_in_rect(s, "소상공인 컨설팅 보고서",
            MARGIN, Inches(1.6), Inches(3.4), Inches(0.38),
            size=11, bold=True, color=WHT,
            fill=RED, align=PP_ALIGN.CENTER)

# main title
txt(s, "역삼효태권도장", MARGIN, Inches(2.2), Inches(10), Inches(1.35),
    size=62, bold=True, color=WHT)

# subtitle rule
rect(s, MARGIN, Inches(3.62), Inches(0.6), Inches(0.04), fill=RED)
txt(s, "온라인 마케팅 진단 및 자립형 마케팅 시스템 구축",
    MARGIN, Inches(3.76), Inches(10), Inches(0.5),
    size=18, color=RGBColor(0x8A, 0xA4, 0xCC))

# meta info block
MY = Inches(4.55)
meta = [
    ("업 체 명",  "역삼효태권도장"),
    ("대    표",  "김형열 관장"),
    ("컨설팅팀",  "B그룹 5조  권용준·손미현"),
    ("기    간",  "2026.05.26 – 2026.05.29  (3일)"),
    ("분    야",  "학원업  |  온라인 마케팅 진단 및 솔루션"),
]
for label, val in meta:
    txt(s, label, MARGIN, MY, Inches(1.3), Inches(0.34),
        size=10, color=RGBColor(0x60, 0x7A, 0xA8), bold=True)
    txt(s, val, MARGIN + Inches(1.45), MY, Inches(7), Inches(0.34),
        size=10, color=RGBColor(0xCC, 0xD8, 0xEE))
    MY += Inches(0.38)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S02 — TABLE OF CONTENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "00", "목차", "Contents")
slide_footer(s, 2)

toc = [
    ("01", "업체 개요",            "역삼효태권도장 기본 정보 및 관원 현황"),
    ("02", "현황 진단 · 핵심 강점", "온라인 마케팅 현황 분석 및 4대 강점 도출"),
    ("03", "1회차 컨설팅",          "브랜드 포지셔닝 및 온라인 전략 수립"),
    ("04", "2회차 컨설팅",          "네이버 플레이스 최적화 · AI 젬스 시스템 구축"),
    ("05", "3회차 컨설팅",          "자립 실습 완료 · 리뷰 성장 계획 · 총정리"),
    ("06", "컨설팅 성과 비교",      "Before → After 전후 비교"),
    ("07", "자립형 마케팅 루틴",    "주 2회 10분 루틴 및 실행 로드맵"),
    ("08", "향후 제언",             "지속가능성 및 성장 전략 제언"),
]

ROW_H = Inches(0.62)
COL_W = (W - MARGIN * 2 - Inches(0.3)) / 2
START_Y = Inches(1.42)

for i, (num, title, desc) in enumerate(toc):
    col = i % 2
    row = i // 2
    X = MARGIN + col * (COL_W + Inches(0.3))
    Y = START_Y + row * (ROW_H + Inches(0.1))
    card(s, X, Y, COL_W, ROW_H)
    # number
    txt(s, num, X + Inches(0.14), Y + Inches(0.10), Inches(0.38), Inches(0.38),
        size=13, bold=True, color=RED)
    # title
    txt(s, title, X + Inches(0.52), Y + Inches(0.07), COL_W - Inches(0.62), Inches(0.3),
        size=12, bold=True, color=TXD)
    # desc
    txt(s, desc, X + Inches(0.52), Y + Inches(0.35), COL_W - Inches(0.62), Inches(0.24),
        size=9, color=TXM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S03 — 업체 개요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "01", "업체 개요", "역삼효태권도장 기본 정보 및 운영 현황")
slide_footer(s, 3)

# ── Left info card ──
LW = Inches(6.2)
card(s, MARGIN, Inches(1.42), LW, Inches(5.72))
label_tag(s, "기본 정보", MARGIN + Inches(0.2), Inches(1.55))

info = [
    ("명칭",     "역삼효태권도장"),
    ("위치",     "서울 강남구 역삼로 14길 18 2층\n역삼역 3번 출구 858m · 역삼초 인근"),
    ("영업시간", "월~금  12:00 – 20:00"),
    ("전화",     "02-552-7582"),
    ("운영인력", "관장 김형열 + 사범 총 2명"),
    ("등록인원", "65명  (유치부 16 · 저학년 23 · 고학년 23 · 중등 3)"),
    ("수강료",   "주 3~4회 월 180,000원  /  주 5회 월 190,000원"),
    ("운영기간", "12년 (인근 3년 + 현 위치 9년)"),
]
IY = Inches(1.82)
for label, val in info:
    txt(s, label, MARGIN + Inches(0.2), IY, Inches(1.2), Inches(0.26),
        size=9, bold=True, color=TXL)
    txt(s, val, MARGIN + Inches(1.45), IY, LW - Inches(1.65), Inches(0.3),
        size=10.5, color=TXD)
    if label != "운영기간":
        divider(s, MARGIN + Inches(0.2), IY + Inches(0.42), LW - Inches(0.35))
    IY += Inches(0.5) if "\n" not in val else Inches(0.65)

# ── Right: stat cards + bar ──
RX = MARGIN + LW + Inches(0.35)
RW = W - RX - Inches(0.35)

# Stat trio
stats = [
    ("65명", "등록 관원"),
    ("12년", "운영 경력"),
    ("6타임", "일일 픽업"),
]
SW = (RW - Inches(0.2)) / 3
SX = RX
for val, lbl in stats:
    card(s, SX, Inches(1.42), SW, Inches(1.05))
    txt(s, val, SX + Inches(0.14), Inches(1.55), SW - Inches(0.2), Inches(0.48),
        size=26, bold=True, color=NAV)
    txt(s, lbl, SX + Inches(0.14), Inches(2.0), SW - Inches(0.2), Inches(0.28),
        size=9, color=TXM)
    SX += SW + Inches(0.1)

# Member composition bar chart
card(s, RX, Inches(2.6), RW, Inches(4.54))
label_tag(s, "관원 구성 현황", RX + Inches(0.2), Inches(2.73))
txt(s, "총 65명 기준", RX + RW - Inches(1.4), Inches(2.73),
    Inches(1.3), Inches(0.22), size=8, color=TXL, align=PP_ALIGN.RIGHT)

bar_items = [
    ("유치부 (7세)",       16, 15.4),
    ("초등 저학년 1~3학년", 23, 35.4),
    ("초등 고학년 4~6학년", 23, 35.4),
    ("중학교",              3,  4.6),
]
MAX_W = RW - Inches(0.4)
BY = Inches(3.08)
for lbl, cnt, pct in bar_items:
    txt(s, lbl, RX + Inches(0.2), BY, Inches(2.1), Inches(0.24),
        size=9, color=TXM)
    # background bar
    rect(s, RX + Inches(2.35), BY + Inches(0.03),
         MAX_W - Inches(2.35) - Inches(0.2), Inches(0.24), fill=BDR)
    # fill bar
    fill_w = (MAX_W - Inches(2.35) - Inches(0.2)) * cnt / 65
    rect(s, RX + Inches(2.35), BY + Inches(0.03), fill_w, Inches(0.24), fill=NAV)
    # label
    txt(s, f"{cnt}명  {pct}%",
        RX + Inches(2.35) + fill_w + Inches(0.06), BY,
        Inches(1.2), Inches(0.26),
        size=9, bold=True, color=TXD)
    BY += Inches(0.52)

# Key insight
rect(s, RX + Inches(0.2), BY + Inches(0.1), RW - Inches(0.35), Inches(0.88),
     fill=BG, line=BDR)
rect(s, RX + Inches(0.2), BY + Inches(0.1), Inches(0.04), Inches(0.88), fill=RED)
txt(s, "고학년·중등 비율 40%\n→ 장기 신뢰 도장의 핵심 경쟁력",
    RX + Inches(0.34), BY + Inches(0.18),
    RW - Inches(0.55), Inches(0.72),
    size=10, bold=True, color=NAV)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S04 — 현황 진단
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "02", "현황 진단", "온라인 마케팅 인프라 및 강약점 분석")
slide_footer(s, 4)

# Two problem cards (equal width)
HCW = (W - MARGIN * 2 - Inches(0.3)) / 2
problems = [
    ("마케팅 인프라 부족",
     ["네이버 플레이스 리뷰 단 13개 (기본 4 / 키워드 7 / 블로그 2)",
      "브랜드명 혼재 — 역삼효태권도장 / 효태권도 병용",
      "채널별 정보 불일치로 검색 신뢰도 분산",
      "온라인 신규 유입 구조 사실상 전무"]),
    ("디지털 활용 역량 저하",
     ["인스타그램 등 SNS 채널 업데이트 미흡",
      "홍보 콘텐츠 자체 제작 경험 부족",
      "학부모 디지털 소통 루틴 부재",
      "마케팅 실행 루틴 전무"]),
]
PX = MARGIN
for title, items in problems:
    card(s, PX, Inches(1.42), HCW, Inches(3.55))
    label_tag(s, "문제 진단", PX + Inches(0.2), Inches(1.55))
    txt(s, title, PX + Inches(0.2), Inches(1.82), HCW - Inches(0.35), Inches(0.38),
        size=15, bold=True, color=NAV)
    divider(s, PX + Inches(0.2), Inches(2.25), HCW - Inches(0.3))
    IY = Inches(2.36)
    for item in items:
        bullet_row(s, item, PX + Inches(0.2), IY, HCW - Inches(0.3))
        IY += Inches(0.42)
    PX += HCW + Inches(0.3)

# Core diagnosis callout
rect(s, MARGIN, Inches(5.1), W - MARGIN * 2, Inches(0.9),
     fill=NAV, line=None)
rect(s, MARGIN, Inches(5.1), Inches(0.055), Inches(0.9), fill=RED)
txt(s, "핵심 진단",
    MARGIN + Inches(0.18), Inches(5.16), Inches(1.5), Inches(0.3),
    size=9, bold=True, color=RED)
txt(s, "오프라인 서비스 품질·학부모 만족도는 매우 높으나, "
       "온라인 검색 결과와 신규 유입 구조로 연결되지 않고 있는 상태",
    MARGIN + Inches(0.18), Inches(5.44), W - MARGIN * 2 - Inches(0.28), Inches(0.46),
    size=12, bold=True, color=WHT)

# Strength chips
strengths = ["12년 장기 운영 신뢰", "6타임 무료 픽업", "실시간 출결 알림",
             "정서적 유대 교육", "고학년 40% 유지"]
SX = MARGIN
SY = Inches(6.14)
for st in strengths:
    SW_s = (W - MARGIN * 2 - Inches(0.2) * 4) / 5
    txt_in_rect(s, st, SX, SY, SW_s, Inches(0.5),
                size=10, bold=True, color=NAV,
                fill=WHT, line=BDR, align=PP_ALIGN.CENTER)
    SX += SW_s + Inches(0.2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S05 — 4대 핵심 강점
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
rect(s, 0, 0, W, H, fill=NAV)
rect(s, 0, 0, Inches(0.08), H, fill=RED)
rect(s, 0, H - Inches(0.04), W, Inches(0.04), fill=RED)
slide_footer(s, 5)

txt(s, "04", MARGIN, Inches(0.28), Inches(0.6), Inches(0.3),
    size=10, bold=True, color=RED)
txt(s, "4대 핵심 강점", MARGIN, Inches(0.55), Inches(10), Inches(0.9),
    size=40, bold=True, color=WHT)
txt(s, "컨설팅 현장 조사를 통해 도출된 역삼효태권도장의 독보적 경쟁력",
    MARGIN, Inches(1.42), Inches(10), Inches(0.36),
    size=13, color=RGBColor(0x8A, 0xA4, 0xCC))
rect(s, MARGIN, Inches(1.82), Inches(0.55), Inches(0.03), fill=RED)

cards_data = [
    ("01", "완벽한 케어",
     ["역삼초 6타임 무료 픽업 (관장 직접 운행)",
      "실시간 에듀패밀리 출결 사진 전송",
      "외주 없는 관장 직접 책임 운영"]),
    ("02", "모두가 주인공",
     ["시범단 위주가 아닌 전원 성장 수업",
      "예절·체력·태권도·생활지도 4축 체계",
      "60분 체계적 수업 설계"]),
    ("03", "통합 교육",
     ["기초체력 / 학교체육 / 태권도 실기",
      "생활지도 통합 60분 수업 구조",
      "정서적 유대 기반 교육 철학"]),
    ("04", "12년의 신뢰",
     ["졸업생이 찾아오고 이사 후에도 다니는 교육력",
      "고학년·중등 비율 40% 유지 (객관적 증거)",
      "\"가랑비에 옷 젖듯이\" 철학"]),
]

CW = (W - MARGIN * 2 - Inches(0.25) * 3) / 4
CX = MARGIN
CH = Inches(4.95)
CY = Inches(2.12)

for num, title, bullets in cards_data:
    # card bg
    rect(s, CX, CY, CW, CH, fill=NAV_LT, line=RGBColor(0x2A, 0x48, 0x7A))
    # red top accent
    rect(s, CX, CY, CW, Inches(0.04), fill=RED)
    # number
    txt(s, num, CX + Inches(0.2), CY + Inches(0.18), CW, Inches(0.38),
        size=24, bold=True, color=RED)
    # title
    txt(s, title, CX + Inches(0.2), CY + Inches(0.6), CW - Inches(0.25), Inches(0.45),
        size=15, bold=True, color=WHT)
    # rule
    rect(s, CX + Inches(0.2), CY + Inches(1.1), CW - Inches(0.35), Inches(0.018),
         fill=RGBColor(0x2A, 0x48, 0x7A))
    # bullets
    BY = CY + Inches(1.26)
    for b in bullets:
        rect(s, CX + Inches(0.2), BY + Inches(0.1),
             Inches(0.05), Inches(0.05), fill=RED)
        txt(s, b, CX + Inches(0.34), BY, CW - Inches(0.5), Inches(0.42),
            size=10, color=RGBColor(0xCC, 0xD8, 0xEE))
        BY += Inches(0.48)
    CX += CW + Inches(0.25)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S06 — 1회차 컨설팅
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "03", "1회차 컨설팅", "2026.05.26 — 브랜드 포지셔닝 및 온라인 전략 수립")
slide_footer(s, 6)

# Positioning statement — full width highlight
rect(s, MARGIN, Inches(1.42), W - MARGIN * 2, Inches(0.82), fill=NAV)
rect(s, MARGIN, Inches(1.42), Inches(0.055), Inches(0.82), fill=RED)
txt(s, "메인 포지셔닝",
    MARGIN + Inches(0.2), Inches(1.5), Inches(2), Inches(0.26),
    size=9, bold=True, color=RED)
txt(s, "\"아이의 마음까지 책임지는  12년 신뢰\"",
    MARGIN + Inches(0.2), Inches(1.74), W - MARGIN * 2 - Inches(0.3), Inches(0.42),
    size=18, bold=True, color=WHT)

# Left — 포지셔닝 상세
LW_6 = Inches(5.8)
card(s, MARGIN, Inches(2.38), LW_6, Inches(4.76))
label_tag(s, "브랜드 전략 확정", MARGIN + Inches(0.2), Inches(2.52))

pos = [
    ("핵심 타깃",   "역삼동 맞벌이 학부모 (안심 케어 + 정서적 성장 동시 요구)"),
    ("브랜드 통일", "모든 채널 「역삼효태권도장 / 02-552-7582」 완전 일원화"),
    ("주요 채널",   "네이버 플레이스 최적화 + 인스타그램 주 2회 10분 루틴"),
    ("핵심 메시지", "\"가랑비에 옷 젖듯이\" — 서두르지 않는 12년 교육 철학"),
]
IY_6 = Inches(2.82)
for label, val in pos:
    txt(s, label, MARGIN + Inches(0.2), IY_6, Inches(1.3), Inches(0.26),
        size=9, bold=True, color=TXL)
    txt(s, val, MARGIN + Inches(1.55), IY_6, LW_6 - Inches(1.7), Inches(0.44),
        size=11, color=TXD)
    IY_6 += Inches(0.62)
    if label != "핵심 메시지":
        divider(s, MARGIN + Inches(0.2), IY_6 - Inches(0.2), LW_6 - Inches(0.3))

# Right — 4 step process
RX_6 = MARGIN + LW_6 + Inches(0.35)
RW_6 = W - RX_6 - Inches(0.35)
card(s, RX_6, Inches(2.38), RW_6, Inches(4.76))
label_tag(s, "1회차 수행 프로세스", RX_6 + Inches(0.2), Inches(2.52))

steps = [
    ("01", "온라인 현황 진단",
     "네이버 플레이스 리뷰 현황\n브랜드명 혼재 및 채널 불일치 확인"),
    ("02", "교육 철학 · 핵심 강점 도출",
     "12년 운영 신뢰도\n정서적 유대 기반 교육 정신 파악"),
    ("03", "4대 핵심 강점 정의",
     "완벽한 케어 / 모두가 주인공\n통합 교육 / 12년의 신뢰"),
    ("04", "브랜드 포지셔닝 확정",
     "메인 포지셔닝 및 타깃 설정\n채널 전략 로드맵 수립 및 공유"),
]
SY_6 = Inches(2.88)
SH_6 = Inches(0.95)
for num, title, desc in steps:
    rect(s, RX_6 + Inches(0.2), SY_6, Inches(0.45), SH_6, fill=NAV)
    txt(s, num, RX_6 + Inches(0.2), SY_6 + Inches(0.28),
        Inches(0.45), Inches(0.38), size=13, bold=True, color=RED, align=PP_ALIGN.CENTER)
    rect(s, RX_6 + Inches(0.68), SY_6, RW_6 - Inches(0.88), SH_6,
         fill=BG, line=BDR)
    txt(s, title, RX_6 + Inches(0.82), SY_6 + Inches(0.06),
        RW_6 - Inches(1.0), Inches(0.32), size=11, bold=True, color=NAV)
    txt(s, desc, RX_6 + Inches(0.82), SY_6 + Inches(0.36),
        RW_6 - Inches(1.0), Inches(0.5), size=9.5, color=TXM)
    SY_6 += SH_6 + Inches(0.1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S07 — 네이버 플레이스 최적화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "04", "네이버 플레이스 전면 최적화", "2회차 컨설팅 2026.05.28 — 검색 최적화 완전 정비")
slide_footer(s, 7)

# Table
T_Y = Inches(1.42)
T_HDR_H = Inches(0.4)
T_ROW_H = Inches(0.72)
T_COLS = [MARGIN, Inches(2.65), Inches(5.55), Inches(9.55)]
T_WIDTHS = [Inches(2.05), Inches(2.85), Inches(3.95), Inches(3.35)]

for i, (lbl, cw) in enumerate(zip(["구분", "변경 전", "변경 후  (최적화 완료)", "효과"], T_WIDTHS)):
    txt_in_rect(s, lbl, T_COLS[i], T_Y, cw, T_HDR_H,
                size=11, bold=True, color=WHT, align=PP_ALIGN.CENTER,
                fill=NAV if i != 2 else RED)

rows = [
    ("공식 상호 및 번호",
     "상호명·대표번호 미통일",
     "역삼효태권도장 / 02-552-7582\n완전 통일",
     "검색 정확도↑\n브랜드 신뢰도↑"),
    ("영업 정보 상태",
     "운영시간 미입력",
     "평일 12:00~20:00 입력\n정확한 상담 유도 시간 적용",
     "상담 전환율↑"),
    ("브랜드 소개글",
     "단순 텍스트 / 매력 미흡",
     "\"가랑비에 옷 젖듯이...\"\n12년 철학 + 무료픽업 + 출결앱 키워드",
     "감성적 신뢰 형성"),
    ("시각 자료 구성",
     "도장 사진 등록 부족",
     "수련·시설·픽업 사진\n신규 업로드 완료",
     "첫인상 신뢰도↑"),
    ("핵심 서비스 노출",
     "핵심 강점 기능 미노출",
     "무료픽업·야간수련·에듀패밀리\n안심케어·체력강화 등록",
     "검색 노출 키워드↑"),
]
TY2 = T_Y + T_HDR_H
for idx, (c0, c1, c2, c3) in enumerate(rows):
    bg2 = WHT if idx % 2 == 0 else BG
    for j, (txt_s, cw) in enumerate(zip([c0, c1, c2, c3], T_WIDTHS)):
        fc = NAV if j == 0 else (GRN if j == 2 else TXD)
        fw = j == 0
        rect(s, T_COLS[j], TY2, cw, T_ROW_H,
             fill=GRN_BG if j == 2 else bg2, line=BDR, lw=Pt(0.5))
        txt(s, txt_s, T_COLS[j] + Inches(0.1), TY2 + Inches(0.08),
            cw - Inches(0.14), T_ROW_H - Inches(0.12),
            size=10, bold=fw, color=fc)
    TY2 += T_ROW_H

# Tip bar
rect(s, MARGIN, TY2 + Inches(0.1), W - MARGIN * 2, Inches(0.42), fill=NAV)
rect(s, MARGIN, TY2 + Inches(0.1), Inches(0.055), Inches(0.42), fill=RED)
txt(s, "☞  무료체험 예약 + 네이버 톡톡 기능 추가 → 예비 관원 학부모 소통 편의성 제고 · 전방위 마케팅 활용 가능",
    MARGIN + Inches(0.2), TY2 + Inches(0.16), W - MARGIN * 2 - Inches(0.28), Inches(0.3),
    size=10.5, bold=True, color=WHT)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S08 — AI 젬스 시스템
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "04", "AI 젬스 자동화 시스템 구축", "제미나이 젬스(Gemini Gems) 3종 + AI 홍보이미지 생성")
slide_footer(s, 8)

gems = [
    ("GEMS 1", "인스타 포스팅\n생성기",
     "사진만 넣으면\n인스타 텍스트 +\n해시태그 자동 생성",
     "주 2회 포스팅\n5분 이내 완성"),
    ("GEMS 2", "리뷰 요청\n카톡 생성기",
     "학부모에게 부담 없는\n개인 맞춤 리뷰 요청\n메시지 자동 작성",
     "3개월 30개 달성\n핵심 도구"),
    ("GEMS 3", "리뷰 답글\n생성기",
     "네이버 리뷰 입력 시\n전문적인 감사 답글\n자동 생성",
     "응답률 100%\n신뢰도 제고"),
    ("AI 이미지", "홍보 이미지\n생성",
     "챗GPT · 제미나이 활용\n아이 초상권 보호\n일러스트 제작",
     "홍보물 외주비\n절감"),
]
GCW = (W - MARGIN * 2 - Inches(0.3) * 3) / 4
GCH = Inches(5.58)
GX = MARGIN
GY = Inches(1.42)

for badge, title, desc, result in gems:
    card(s, GX, GY, GCW, GCH)
    # header band inside card
    rect(s, GX + Inches(0.055), GY, GCW - Inches(0.055), Inches(0.52), fill=NAV)
    txt(s, badge, GX + Inches(0.18), GY + Inches(0.1),
        GCW - Inches(0.3), Inches(0.35), size=12, bold=True, color=RED)
    # title
    txt(s, title, GX + Inches(0.18), GY + Inches(0.66),
        GCW - Inches(0.28), Inches(0.7), size=14, bold=True, color=NAV)
    divider(s, GX + Inches(0.18), GY + Inches(1.44), GCW - Inches(0.3))
    # desc
    DY = GY + Inches(1.58)
    for line in desc.split("\n"):
        txt(s, line, GX + Inches(0.18), DY, GCW - Inches(0.28), Inches(0.34),
            size=10.5, color=TXD)
        DY += Inches(0.36)
    # result footer
    rect(s, GX + Inches(0.055), GY + GCH - Inches(0.88),
         GCW - Inches(0.055), Inches(0.88), fill=NAV)
    txt(s, result,
        GX + Inches(0.18), GY + GCH - Inches(0.82),
        GCW - Inches(0.25), Inches(0.75),
        size=11, bold=True, color=WHT, align=PP_ALIGN.CENTER)
    GX += GCW + Inches(0.3)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S09 — 관원 구성 데이터 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "04", "관원 구성 데이터 분석", "출석부 기반 연령별 분석 → 마케팅 타깃 전략 반영")
slide_footer(s, 9)

# Table (left)
TW = Inches(7.2)
card(s, MARGIN, Inches(1.42), TW, Inches(5.72))
label_tag(s, "연령별 관원 현황", MARGIN + Inches(0.2), Inches(1.55))

cols_x = [MARGIN + Inches(0.18), MARGIN + Inches(1.78), MARGIN + Inches(2.75),
          MARGIN + Inches(3.55)]
cols_w = [Inches(1.55), Inches(0.92), Inches(0.75), TW - Inches(3.7)]
hdrs   = ["연령대", "인원", "비율", "마케팅 포인트"]

THY = Inches(1.82)
for j, (hdr, cw) in enumerate(zip(hdrs, cols_w)):
    txt(s, hdr, cols_x[j], THY, cw, Inches(0.28),
        size=9, bold=True, color=TXL)
divider(s, MARGIN + Inches(0.18), THY + Inches(0.28), TW - Inches(0.3))

member_table = [
    ("7세",          "10명", "15.4%", "초등 입학 준비 전문성 어필"),
    ("1·2학년",       "12명", "18.5%", "기초 체력 형성기 집중 케어"),
    ("3학년",        "11명", "16.9%", "기초 체력 단단한 허리층 타깃"),
    ("4·5·6학년",    "29명", "44.6%", "학교 체육·교우관계 연계 부각"),
    ("중학교",         "3명",  "4.6%", "장기 신뢰 극대화 유지 전략"),
    ("합계",         "65명", "100%",  "역삼동 중심가 안정적 운영 증명"),
]
TRY = THY + Inches(0.32)
for i, (age, cnt, pct, tip) in enumerate(member_table):
    is_last = i == len(member_table) - 1
    bg3 = NAV if is_last else (BG if i % 2 == 0 else WHT)
    fc_base = WHT if is_last else TXD
    for j, (tv, cw) in enumerate(zip([age, cnt, pct, tip], cols_w)):
        fc = (RED if j == 0 and not is_last else
              WHT if is_last else TXD)
        fw = j == 0 or is_last
        rect(s, cols_x[j], TRY, cw, Inches(0.52), fill=bg3)
        txt(s, tv, cols_x[j] + Inches(0.04), TRY + Inches(0.1),
            cw - Inches(0.06), Inches(0.35),
            size=10.5, bold=fw, color=fc,
            align=PP_ALIGN.CENTER if j < 3 else PP_ALIGN.LEFT)
    TRY += Inches(0.52)

# Right — bar chart
RX_9 = MARGIN + TW + Inches(0.35)
RW_9 = W - RX_9 - Inches(0.35)
card(s, RX_9, Inches(1.42), RW_9, Inches(5.72))
label_tag(s, "연령별 비율 시각화", RX_9 + Inches(0.2), Inches(1.55))

bars = [
    ("7세",         15.4), ("1·2학년",    18.5),
    ("3학년",       16.9), ("4~6학년",    44.6),
    ("중학교",       4.6),
]
MAX_PCT = 50
MAX_W_9 = RW_9 - Inches(0.4)
BY_9 = Inches(1.88)
for lbl, pct in bars:
    txt(s, lbl, RX_9 + Inches(0.2), BY_9, Inches(1.1), Inches(0.24),
        size=9, color=TXM)
    bw = MAX_W_9 * pct / MAX_PCT
    rect(s, RX_9 + Inches(1.35), BY_9 + Inches(0.03),
         MAX_W_9 - Inches(1.35), Inches(0.24), fill=BDR)
    rect(s, RX_9 + Inches(1.35), BY_9 + Inches(0.03), bw, Inches(0.24), fill=NAV)
    txt(s, f"{pct}%",
        RX_9 + Inches(1.35) + bw + Inches(0.06), BY_9,
        Inches(0.6), Inches(0.26), size=9, bold=True, color=TXD)
    BY_9 += Inches(0.52)

rect(s, RX_9 + Inches(0.2), BY_9 + Inches(0.22),
     RW_9 - Inches(0.35), Inches(1.55), fill=NAV)
rect(s, RX_9 + Inches(0.2), BY_9 + Inches(0.22), Inches(0.04), Inches(1.55), fill=RED)
txt(s, "고학년 40% 유지율",
    RX_9 + Inches(0.38), BY_9 + Inches(0.32), RW_9 - Inches(0.6), Inches(0.36),
    size=13, bold=True, color=RED)
txt(s, "일반적으로 학과 공부로 이탈하는\n연령대가 전체의 40%를 차지\n→ \"한 번 믿으면 끝까지\" 신뢰 도장의\n   가장 강력한 객관적 마케팅 근거",
    RX_9 + Inches(0.38), BY_9 + Inches(0.72), RW_9 - Inches(0.6), Inches(0.95),
    size=10, color=RGBColor(0xCC, 0xD8, 0xEE))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S10 — 3회차 컨설팅
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "05", "3회차 컨설팅", "2026.05.29 — 자립 실습 완료 · 리뷰 성장 계획 · 시스템 총정리")
slide_footer(s, 10)

# Left — 자립 실습
LW_10 = Inches(6.0)
card(s, MARGIN, Inches(1.42), LW_10, Inches(5.72))
label_tag(s, "관장님 자립 실습 완료", MARGIN + Inches(0.2), Inches(1.55))
txt(s, "5분 루틴 완전 체득 확인",
    MARGIN + Inches(0.2), Inches(1.82), LW_10 - Inches(0.3), Inches(0.34),
    size=13, bold=True, color=NAV)

practice = [
    ("젬스 3번  리뷰 답글 생성기 활용",
     "네이버 플레이스 기존 리뷰 답글 실제 등록 완료"),
    ("젬스 1번  인스타 포스팅 생성기 활용",
     "인스타그램 2번째 포스팅 업로드 · 품질 조정 완료"),
    ("5분 이내 완성 루틴 체득",
     "사진(1분) → 젬스 문구(2분) → 업로드(2분) = 5분"),
    ("네이버 플레이스 보완",
     "무료체험 예약 + 네이버 톡톡 기능 추가"),
    ("AI 홍보 이미지 생성 실습",
     "챗GPT·제미나이 활용 초상권 보호 일러스트 제작"),
]
PY_10 = Inches(2.3)
for title, desc in practice:
    rect(s, MARGIN + Inches(0.2), PY_10 + Inches(0.08),
         Inches(0.12), Inches(0.12), fill=GRN)
    txt(s, title, MARGIN + Inches(0.42), PY_10,
        LW_10 - Inches(0.55), Inches(0.28), size=11, bold=True, color=TXD)
    txt(s, desc, MARGIN + Inches(0.42), PY_10 + Inches(0.28),
        LW_10 - Inches(0.55), Inches(0.26), size=9.5, color=TXM)
    divider(s, MARGIN + Inches(0.2), PY_10 + Inches(0.58), LW_10 - Inches(0.3))
    PY_10 += Inches(0.66)

# Right — 리뷰 성장 계획
RX_10 = MARGIN + LW_10 + Inches(0.35)
RW_10 = W - RX_10 - Inches(0.35)
card(s, RX_10, Inches(1.42), RW_10, Inches(5.72))
label_tag(s, "리뷰 30개 달성 실행 계획", RX_10 + Inches(0.2), Inches(1.55))
txt(s, "3개월 단계별 실행",
    RX_10 + Inches(0.2), Inches(1.82), RW_10 - Inches(0.3), Inches(0.34),
    size=13, bold=True, color=NAV)

# Progress bar
BAR_Y = Inches(2.32)
BAR_W = RW_10 - Inches(0.35)
rect(s, RX_10 + Inches(0.2), BAR_Y, BAR_W, Inches(0.36), fill=BDR)
rect(s, RX_10 + Inches(0.2), BAR_Y, BAR_W * 13 / 30, Inches(0.36), fill=NAV)
txt(s, "현재 13개",
    RX_10 + Inches(0.28), BAR_Y + Inches(0.07), Inches(1.2), Inches(0.24),
    size=9, bold=True, color=WHT)
txt(s, "목표 30개",
    RX_10 + Inches(0.2) + BAR_W - Inches(1.0), BAR_Y - Inches(0.28),
    Inches(1.0), Inches(0.24), size=9, color=TXM, align=PP_ALIGN.RIGHT)

timings = [
    ("신규 등록 1개월 후", "적응 완료 → 만족도 최고점"),
    ("승급 심사 직후",     "성취감 최고조 → 긍정 리뷰 자연 유도"),
    ("야간수련·이벤트 직후", "특별 경험 → 감동 공유 욕구"),
    ("학부모 감사 표현 시", "자발적 만족 → 최적 요청 타이밍"),
]
TY_10 = Inches(2.88)
txt(s, "최적 리뷰 요청 타이밍",
    RX_10 + Inches(0.2), TY_10, RW_10 - Inches(0.3), Inches(0.26),
    size=9, bold=True, color=TXL)
TY_10 += Inches(0.3)
for timing, reason in timings:
    rect(s, RX_10 + Inches(0.2), TY_10, Inches(0.04), Inches(0.68), fill=RED)
    txt(s, timing, RX_10 + Inches(0.38), TY_10 + Inches(0.04),
        RW_10 - Inches(0.55), Inches(0.3), size=11, bold=True, color=TXD)
    txt(s, reason, RX_10 + Inches(0.38), TY_10 + Inches(0.34),
        RW_10 - Inches(0.55), Inches(0.28), size=9.5, color=TXM)
    TY_10 += Inches(0.76)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S11 — Before / After 성과 비교
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "06", "컨설팅 성과 비교", "Before → After  전후 비교")
slide_footer(s, 11)

BA_COLS = [MARGIN, Inches(2.75), Inches(7.3)]
BA_WIDTHS = [Inches(2.15), Inches(4.5), Inches(4.5)]

# header row
txt_in_rect(s, "항목", BA_COLS[0], Inches(1.42), BA_WIDTHS[0], Inches(0.42),
            size=11, bold=True, color=WHT, fill=NAV, align=PP_ALIGN.CENTER)
txt_in_rect(s, "BEFORE  컨설팅 이전", BA_COLS[1], Inches(1.42), BA_WIDTHS[1], Inches(0.42),
            size=11, bold=True, color=WHT, fill=RGBColor(0x8A, 0x0E, 0x20),
            align=PP_ALIGN.CENTER)
txt_in_rect(s, "AFTER  컨설팅 이후", BA_COLS[2], Inches(1.42), BA_WIDTHS[2], Inches(0.42),
            size=11, bold=True, color=WHT, fill=GRN, align=PP_ALIGN.CENTER)

ba_rows = [
    ("네이버 플레이스\n운영",
     "운영 미흡\n리뷰 댓글·소식·정보 불일치",
     "전면 정비 완료\n메뉴·콘텐츠·댓글·소식 업데이트"),
    ("마케팅\n문구 작성",
     "인스타/블로그 문구\n자체 작성 불가",
     "AI 젬스 3종 + 매뉴얼 제공\n클릭 한 번으로 자동 생성"),
    ("홍보물\n제작",
     "홍보물 자체 제작\n완전 불가",
     "챗GPT·제미나이 활용\n초상권 보호 일러스트 자유 제작"),
    ("마케팅\n실행 루틴",
     "마케팅 루틴\n전무",
     "주 2회 10분 루틴 확립\n촬영 1분+젬스 2분+업로드 2분"),
]
ROW_H_BA = Inches(1.14)
CUR_Y = Inches(1.84)
for i, (label, before, after) in enumerate(ba_rows):
    bg_alt = WHT if i % 2 == 0 else BG
    # label
    rect(s, BA_COLS[0], CUR_Y, BA_WIDTHS[0], ROW_H_BA,
         fill=BG, line=BDR, lw=Pt(0.5))
    txt(s, label, BA_COLS[0] + Inches(0.1), CUR_Y + Inches(0.22),
        BA_WIDTHS[0] - Inches(0.15), Inches(0.7),
        size=11, bold=True, color=NAV, align=PP_ALIGN.CENTER)
    # before
    rect(s, BA_COLS[1], CUR_Y, BA_WIDTHS[1], ROW_H_BA,
         fill=RED_BG, line=BDR, lw=Pt(0.5))
    txt(s, before, BA_COLS[1] + Inches(0.15), CUR_Y + Inches(0.18),
        BA_WIDTHS[1] - Inches(0.2), ROW_H_BA - Inches(0.24),
        size=10.5, color=TXD)
    # arrow
    txt(s, "→", Inches(6.85), CUR_Y + Inches(0.38), Inches(0.4), Inches(0.38),
        size=18, bold=True, color=NAV, align=PP_ALIGN.CENTER)
    # after
    rect(s, BA_COLS[2], CUR_Y, BA_WIDTHS[2], ROW_H_BA,
         fill=GRN_BG, line=BDR, lw=Pt(0.5))
    txt(s, after, BA_COLS[2] + Inches(0.15), CUR_Y + Inches(0.18),
        BA_WIDTHS[2] - Inches(0.2), ROW_H_BA - Inches(0.24),
        size=10.5, bold=True, color=GRN)
    CUR_Y += ROW_H_BA + Inches(0.06)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S12 — 자립형 마케팅 루틴
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "07", "자립형 마케팅 루틴", "주 2회 10분 루틴 — 컨설팅 이후에도 지속 가능한 성장")
slide_footer(s, 12)

# 5 step flow
steps_r = [
    ("01\n사진 촬영", "1분",  "수련 뒷모습\n시설 모습"),
    ("02\n젬스 문구", "2분",  "인스타 텍스트\n해시태그 자동"),
    ("03\n업로드",    "2분",  "인스타그램\n포스팅 완성"),
    ("04\n리뷰 요청", "수시", "젬스 2번 활용\n맞춤 카톡"),
    ("05\n리뷰 답글", "즉시", "젬스 3번 활용\n자동 생성"),
]
SCW = (W - MARGIN * 2 - Inches(0.22) * 4) / 5
SCH = Inches(2.55)
SX_R = MARGIN
SY_R = Inches(1.42)

for i, (label, time, desc) in enumerate(steps_r):
    card(s, SX_R, SY_R, SCW, SCH)
    rect(s, SX_R + Inches(0.055), SY_R, SCW - Inches(0.055), Inches(0.42), fill=NAV)
    txt(s, time, SX_R + Inches(0.14), SY_R + Inches(0.08),
        SCW - Inches(0.25), Inches(0.28), size=11, bold=True, color=RED)
    txt(s, label, SX_R + Inches(0.14), SY_R + Inches(0.55),
        SCW - Inches(0.25), Inches(0.68), size=12, bold=True, color=NAV)
    divider(s, SX_R + Inches(0.14), SY_R + Inches(1.3), SCW - Inches(0.25))
    for j, line in enumerate(desc.split("\n")):
        txt(s, line, SX_R + Inches(0.14), SY_R + Inches(1.44) + j * Inches(0.38),
            SCW - Inches(0.25), Inches(0.35), size=10, color=TXM)
    # connector
    if i < 4:
        txt(s, "›", SX_R + SCW + Inches(0.04), SY_R + Inches(0.95),
            Inches(0.18), Inches(0.4), size=22, bold=True, color=NAV,
            align=PP_ALIGN.CENTER)
    SX_R += SCW + Inches(0.22)

# Total time callout
rect(s, MARGIN, Inches(4.12), W - MARGIN * 2, Inches(0.52), fill=NAV)
rect(s, MARGIN, Inches(4.12), Inches(0.055), Inches(0.52), fill=RED)
txt(s, "총 5분 이내 완성  —  스마트폰 하나로 전문적인 마케팅 콘텐츠 제작 가능",
    MARGIN + Inches(0.2), Inches(4.2), W - MARGIN * 2 - Inches(0.3), Inches(0.38),
    size=14, bold=True, color=WHT)

# 4 monthly checklist cards
chk_data = [
    ("네이버 플레이스",  ["정보 최신화", "리뷰 답글 등록", "소식 게시"]),
    ("인스타그램",       ["주 2회 포스팅", "해시태그 최적화", "팔로워 소통"]),
    ("리뷰 관리",        ["개별 요청 발송", "답글 즉시 등록", "30개 목표 진행"]),
    ("환경개선",         ["계단·복도 청결", "비포·애프터 기록", "학부모 첫인상 관리"]),
]
CCW = (W - MARGIN * 2 - Inches(0.3) * 3) / 4
CCX = MARGIN
for ctitle, citems in chk_data:
    card(s, CCX, Inches(4.8), CCW, Inches(2.28))
    txt(s, ctitle, CCX + Inches(0.18), Inches(4.94),
        CCW - Inches(0.25), Inches(0.3), size=11, bold=True, color=NAV)
    divider(s, CCX + Inches(0.18), Inches(5.28), CCW - Inches(0.28))
    CIY = Inches(5.38)
    for ci in citems:
        rect(s, CCX + Inches(0.18), CIY + Inches(0.08),
             Inches(0.05), Inches(0.05), fill=GRN)
        txt(s, ci, CCX + Inches(0.32), CIY, CCW - Inches(0.42), Inches(0.3),
            size=9.5, color=TXD)
        CIY += Inches(0.34)
    CCX += CCW + Inches(0.3)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S13 — 자립 시스템 총정리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "05", "자립 시스템 총정리", "컨설팅 종료 시점 구축 완료 현황")
slide_footer(s, 13)

items_13 = [
    ("네이버 플레이스 최적화 및 업데이트",
     "브랜드 통일·운영시간·소개글·사진·핵심 서비스 전면 정비 / "
     "무료체험 예약 + 네이버 톡톡 추가 → 예비 관원 소통 채널 확보"),
    ("인스타그램 공식 채널 정상 가동",
     "역삼효태권도장 공식 인스타그램 개설·프로필 구성·첫 포스팅 완료 / "
     "관장님 직접 실습으로 지속 운영 역량 확보"),
    ("AI 젬스 4종 완전 체득 및 실습 완료",
     "인스타 포스팅 생성기 / 리뷰 요청 카톡 생성기 / 리뷰 답글 생성기 / AI 홍보이미지 생성 "
     "→ 젬스 활용 매뉴얼 제작 및 숙지 확인"),
    ("주 2회 10분 마케팅 루틴 확립",
     "사진 촬영(1분) + 젬스 활용(2분) + 업로드(2분) = 5분 이내 완성 루틴 / "
     "외부 대행 없이 스스로 운영 가능한 자립형 마케팅 시스템"),
    ("리뷰 30개 달성 단계별 실행 계획 수립",
     "현재 13개 → 3개월 내 30개 목표 / 최적 타이밍별 요청 전략 확정 / "
     "젬스 2번 개별 맞춤 발송으로 강요 없는 리뷰 확보"),
    ("환경개선 및 학부모 눈높이 소통 의지 제고",
     "계단·복도 청결 환경개선 (첫인상 관리) / "
     "서울시 소상공인 지원사업 연계 시설개선 300만원 지원 안내"),
]
IY_13 = Inches(1.42)
for title, desc in items_13:
    RH_13 = Inches(0.82)
    rect(s, MARGIN, IY_13, W - MARGIN * 2, RH_13,
         fill=WHT, line=BDR, lw=Pt(0.75))
    rect(s, MARGIN, IY_13, Inches(0.055), RH_13, fill=RED)
    # check
    txt_in_rect(s, "✓", MARGIN + Inches(0.1), IY_13 + Inches(0.18),
                Inches(0.36), Inches(0.46),
                size=15, bold=True, color=WHT, fill=GRN, align=PP_ALIGN.CENTER)
    txt(s, title, MARGIN + Inches(0.6), IY_13 + Inches(0.08),
        Inches(5.5), Inches(0.32), size=12, bold=True, color=NAV)
    txt(s, desc, MARGIN + Inches(0.6), IY_13 + Inches(0.4),
        W - MARGIN * 2 - Inches(0.72), Inches(0.36),
        size=9.5, color=TXM)
    IY_13 += RH_13 + Inches(0.07)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S14 — 향후 제언
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
bg(s)
slide_header(s, "08", "향후 제언", "지속 가능성 및 성장 전략 제언")
slide_footer(s, 14)

recs_14 = [
    ("01", "단톡방 유지 사후 관리",
     "컨설팅 팀과 단체 채팅방 유지로 추후 궁금증 즉시 해결\n지속적인 관리 및 피드백 제공 예정"),
    ("02", "WOM 입소문 마케팅",
     "컨설팅 수혜 업체가 주변 소상공인 대상 홍보\n→ 추천제도 운영으로 선순환 생태계 구축 제언"),
    ("03", "서울시 지원사업 연계",
     "서울특별시 소상공인 지원사업 활용 (seoulsbdc.or.kr)\n하반기 시설개선 지원 최대 300만원 → 환경개선 비용 절감"),
    ("04", "콘텐츠 자산 지속 축적",
     "수련 사진·영상 꾸준한 기록 → 인스타·네이버 콘텐츠 자산화\n\"가랑비에 옷 젖듯이\" 철학을 온라인에서도 실현"),
]

R14_W = (W - MARGIN * 2 - Inches(0.3)) / 2
R14_H = Inches(2.1)
for i, (num, title, desc) in enumerate(recs_14):
    CX_14 = MARGIN if i % 2 == 0 else MARGIN + R14_W + Inches(0.3)
    CY_14 = Inches(1.42) if i < 2 else Inches(3.66)
    card(s, CX_14, CY_14, R14_W, R14_H)
    txt(s, num, CX_14 + Inches(0.18), CY_14 + Inches(0.14),
        Inches(0.45), Inches(0.35), size=18, bold=True, color=RED)
    txt(s, title, CX_14 + Inches(0.64), CY_14 + Inches(0.18),
        R14_W - Inches(0.82), Inches(0.38), size=13, bold=True, color=NAV)
    divider(s, CX_14 + Inches(0.18), CY_14 + Inches(0.62), R14_W - Inches(0.3))
    for j, line in enumerate(desc.split("\n")):
        txt(s, line, CX_14 + Inches(0.18), CY_14 + Inches(0.76) + j * Inches(0.38),
            R14_W - Inches(0.3), Inches(0.36), size=10.5, color=TXD)

# Quote block
rect(s, MARGIN, Inches(5.92), W - MARGIN * 2, Inches(1.0), fill=NAV)
rect(s, MARGIN, Inches(5.92), Inches(0.055), Inches(1.0), fill=RED)
txt(s, "관장님 소회",
    MARGIN + Inches(0.2), Inches(5.98), Inches(1.5), Inches(0.26),
    size=9, bold=True, color=RED)
txt(s, "\"태권도 학원들이 대체로 홍보 마케팅과 거리가 멀었는데, "
       "3일 동안 완전히! 꼭 필요한 것을 너무나도 꽉꽉 채워주셨습니다.  감사합니다!\"",
    MARGIN + Inches(0.2), Inches(6.2), W - MARGIN * 2 - Inches(0.3), Inches(0.58),
    size=12, bold=True, color=WHT)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S15 — CLOSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
rect(s, 0, 0, W, H, fill=NAV)
rect(s, 0, 0, Inches(0.08), H, fill=RED)
rect(s, 0, H - Inches(0.06), W, Inches(0.06), fill=RED)
oval(s, W - Inches(5.5), Inches(-1.8), Inches(7), Inches(7),
     RGBColor(0x12, 0x26, 0x4E))

txt(s, "감사합니다", MARGIN, Inches(1.6), Inches(10), Inches(1.5),
    size=64, bold=True, color=WHT)
rect(s, MARGIN, Inches(3.12), Inches(0.65), Inches(0.04), fill=RED)
txt(s, "역삼효태권도장  온라인 마케팅 컨설팅 보고서",
    MARGIN, Inches(3.26), Inches(10), Inches(0.48),
    size=16, color=RGBColor(0x8A, 0xA4, 0xCC))

summary = [
    "네이버 플레이스 완전 최적화 및 브랜드 통일",
    "인스타그램 공식 채널 개설 및 첫 포스팅 완료",
    "AI 젬스 3종 자동화 시스템 완전 체득",
    "주 2회 10분 마케팅 루틴 자립 시스템 완성",
    "3개월 리뷰 30개 달성 단계별 실행 계획 수립",
]
SY_15 = Inches(4.0)
for pt in summary:
    rect(s, MARGIN, SY_15 + Inches(0.1), Inches(0.04), Inches(0.12), fill=RED)
    txt(s, pt, MARGIN + Inches(0.18), SY_15,
        Inches(8), Inches(0.34), size=12, color=RGBColor(0xCC, 0xD8, 0xEE))
    SY_15 += Inches(0.42)

rect(s, MARGIN, H - Inches(1.1), Inches(7.5), Inches(0.6),
     fill=NAV_LT)
rect(s, MARGIN, H - Inches(1.1), Inches(0.04), Inches(0.6), fill=RED)
txt(s, "B그룹 5조  권용준·손미현  |  2026.05.26 – 2026.05.29",
    MARGIN + Inches(0.2), H - Inches(1.0), Inches(7), Inches(0.4),
    size=11, color=RGBColor(0x8A, 0xA4, 0xCC))

# ── Save ────────────────────────────────────────────────────────────────────────
OUT = "/home/user/-/역삼효태권도장_온라인마케팅컨설팅_보고서.pptx"
prs.save(OUT)
print(f"Saved: {OUT}")
