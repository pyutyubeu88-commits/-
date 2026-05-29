"""
역삼효태권도장 컨설팅 보고서 PPT v3
Design rules:
- All content fills CY → CB (no dead bottom space)
- Cards: white + BDR border + 5px RED left bar
- Dark cards: NAV_LT fill + 3px RED top bar
- 2-color palette: NAV + RED only
- Typography: 28pt title / 13pt subhead / 11pt body / 9pt caption
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

NAV    = RGBColor(0x0D, 0x1B, 0x3E)
RED    = RGBColor(0xC8, 0x10, 0x2E)
WHT    = RGBColor(0xFF, 0xFF, 0xFF)
BG     = RGBColor(0xF4, 0xF6, 0xFA)
BDR    = RGBColor(0xD8, 0xE2, 0xEE)
TXD    = RGBColor(0x1E, 0x2A, 0x3A)
TXM    = RGBColor(0x54, 0x6E, 0x7A)
TXL    = RGBColor(0x90, 0xA4, 0xAE)
GRN    = RGBColor(0x14, 0x7A, 0x3E)
NAV_LT = RGBColor(0x14, 0x2A, 0x58)
NAV_DIM= RGBColor(0x0A, 0x14, 0x2E)
RED_BG = RGBColor(0xFD, 0xEE, 0xF1)
GRN_BG = RGBColor(0xED, 0xFB, 0xF4)
STRIPE = RGBColor(0xEA, 0xF0, 0xF8)

W  = Inches(13.33)
H  = Inches(7.5)
M  = Inches(0.38)
HDR= Inches(1.14)
FTR= Inches(0.28)
CY = HDR + Inches(0.08)   # 1.22"
CB = H - FTR - Inches(0.06)  # 7.16"
CH = CB - CY               # 5.94"
IG = Inches(0.2)           # inter-gap

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]

# ── primitives ─────────────────────────────────────────────────────────────────
def sl(): return prs.slides.add_slide(BLANK)

def R(s, l, t, w, h, fill=None, line=None, lw=Pt(0.75)):
    sh = s.shapes.add_shape(1, l, t, w, h)
    sh.fill.solid() if fill else sh.fill.background()
    if fill: sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line if line else RGBColor(0,0,0)
    if line: sh.line.width = lw
    else: sh.line.fill.background()
    return sh

def OV(s, l, t, w, h, fill):
    sh = s.shapes.add_shape(9, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background(); return sh

def T(s, text, l, t, w, h, size=11, bold=False, color=TXD,
      align=PP_ALIGN.LEFT, italic=False):
    b  = s.shapes.add_textbox(l, t, w, h)
    tf = b.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.italic = italic
    return b

def TR(s, text, l, t, w, h, size=11, bold=False, color=TXD,
       align=PP_ALIGN.LEFT, fill=None, line=None, lw=Pt(0.75)):
    sh = R(s, l, t, w, h, fill=fill, line=line, lw=lw)
    tf = sh.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return sh

def div(s, l, t, w): R(s, l, t, w, Inches(0.015), fill=BDR)

# ── layout components ──────────────────────────────────────────────────────────
def page_bg(s): R(s, 0, 0, W, H, fill=BG)

def header(s, num, title, sub=None):
    R(s, 0, 0, W, Inches(0.04), fill=RED)
    R(s, 0, Inches(0.04), W, HDR - Inches(0.04), fill=NAV)
    # section pill
    TR(s, num, M, Inches(0.26), Inches(0.54), Inches(0.46),
       size=12, bold=True, color=WHT, fill=RED, align=PP_ALIGN.CENTER)
    T(s, title, M + Inches(0.66), Inches(0.22), W - M*2, Inches(0.58),
      size=26, bold=True, color=WHT)
    if sub:
        T(s, sub, M + Inches(0.66), Inches(0.78), W - M*2, Inches(0.28),
          size=10, color=RGBColor(0x7A, 0x99, 0xCC), italic=True)

def footer(s, n):
    R(s, 0, H - FTR, W, FTR, fill=NAV)
    T(s, "역삼효태권도장  |  온라인 마케팅 컨설팅 보고서  |  2026.05",
      M, H - FTR + Inches(0.05), Inches(9), FTR,
      size=8, color=RGBColor(0x55, 0x70, 0xA0))
    T(s, str(n), W - Inches(0.55), H - FTR + Inches(0.05),
      Inches(0.42), FTR, size=8, color=RGBColor(0x55, 0x70, 0xA0),
      align=PP_ALIGN.RIGHT)

def card(s, l, t, w, h, accent=RED):
    R(s, l, t, w, h, fill=WHT, line=BDR, lw=Pt(0.75))
    R(s, l, t, Inches(0.055), h, fill=accent)

def dark_card(s, l, t, w, h):
    R(s, l, t, w, h, fill=NAV_LT, line=RGBColor(0x28, 0x48, 0x80))
    R(s, l, t, w, Inches(0.04), fill=RED)

def clabel(s, text, l, t):
    T(s, text.upper(), l, t, Inches(3), Inches(0.2),
      size=8, bold=True, color=RED)

def hdiv(s, l, t, w):
    div(s, l, t, w)

def callout(s, l, t, w, h, text, label=None):
    R(s, l, t, w, h, fill=NAV)
    R(s, l, t, Inches(0.055), h, fill=RED)
    if label:
        T(s, label, l + Inches(0.14), t + Inches(0.08),
          Inches(2), Inches(0.22), size=8, bold=True, color=RED)
    T(s, text, l + Inches(0.14), t + (Inches(0.28) if label else Inches(0.12)),
      w - Inches(0.22), h - (Inches(0.34) if label else Inches(0.2)),
      size=11.5, bold=True, color=WHT)

def bullet(s, text, l, t, w, c=RED, size=11):
    R(s, l, t + Inches(0.1), Inches(0.06), Inches(0.06), fill=c)
    T(s, text, l + Inches(0.14), t, w - Inches(0.14), Inches(0.36),
      size=size, color=TXD)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S01 COVER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
R(s, 0, 0, W, H, fill=NAV)
R(s, 0, 0, Inches(0.1), H, fill=RED)
R(s, 0, H - Inches(0.06), W, Inches(0.06), fill=RED)
# bg circles
OV(s, W - Inches(5.8), Inches(-2.0), Inches(7.5), Inches(7.5), NAV_DIM)
OV(s, W - Inches(3.0), H - Inches(3.5), Inches(5), Inches(5), RGBColor(0x08,0x10,0x24))
OV(s, Inches(1.5), H - Inches(3.2), Inches(3), Inches(3), RGBColor(0x10,0x1E,0x40))

# eyebrow
TR(s, "소상공인 컨설팅 보고서",
   M + Inches(0.1), Inches(1.5), Inches(3.2), Inches(0.38),
   size=11, bold=True, color=WHT, fill=RED, align=PP_ALIGN.CENTER)

T(s, "역삼효태권도장", M + Inches(0.1), Inches(2.0), Inches(11), Inches(1.5),
  size=64, bold=True, color=WHT)
T(s, "온라인 마케팅 진단  ·  자립형 마케팅 시스템 구축",
  M + Inches(0.1), Inches(3.58), Inches(10), Inches(0.46),
  size=17, color=RGBColor(0x80, 0xA0, 0xCC))
R(s, M + Inches(0.1), Inches(4.14), Inches(0.7), Inches(0.04), fill=RED)

# meta card
R(s, M + Inches(0.1), Inches(4.38), Inches(6.4), Inches(2.42), fill=NAV_LT,
  line=RGBColor(0x28, 0x48, 0x80))
R(s, M + Inches(0.1), Inches(4.38), Inches(0.055), Inches(2.42), fill=RED)
meta = [
    ("업 체 명", "역삼효태권도장"),
    ("대    표", "김형열 관장"),
    ("컨설팅팀", "B그룹 5조  권용준 · 손미현"),
    ("기    간", "2026.05.26 – 2026.05.29  (3일 / 총 12시간)"),
    ("테    마", "온라인 마케팅 진단 및 홍보 콘텐츠 솔루션 제공"),
]
MY = Inches(4.56)
for lbl, val in meta:
    T(s, lbl, M + Inches(0.3), MY, Inches(1.3), Inches(0.36),
      size=10, bold=True, color=RGBColor(0x7A, 0x99, 0xCC))
    T(s, val, M + Inches(1.68), MY, Inches(4.6), Inches(0.36),
      size=10, color=RGBColor(0xCC, 0xD8, 0xEE))
    MY += Inches(0.4)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S02 TOC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "00", "목차", "Contents")
footer(s, 2)

toc = [
    ("01","업체 개요",           "역삼효태권도장 기본 정보 및 관원 현황"),
    ("02","현황 진단 · 핵심 강점","온라인 마케팅 현황 분석 및 4대 강점 도출"),
    ("03","1회차 컨설팅",         "브랜드 포지셔닝 및 온라인 전략 수립"),
    ("04","2회차 컨설팅",         "네이버 플레이스 최적화 · AI 젬스 시스템 구축"),
    ("05","3회차 컨설팅",         "자립 실습 완료 · 리뷰 성장 계획 · 총정리"),
    ("06","컨설팅 성과 비교",     "Before → After 전후 비교"),
    ("07","자립형 마케팅 루틴",   "주 2회 10분 루틴 및 실행 로드맵"),
    ("08","향후 제언",            "지속가능성 및 성장 전략 제언"),
]
CW2 = (W - M*2 - IG) / 2
RH  = (CH - IG*3) / 4
for i, (num, title, desc) in enumerate(toc):
    col = i % 2; row = i // 2
    x = M + col*(CW2 + IG)
    y = CY + row*(RH + IG)
    card(s, x, y, CW2, RH)
    TR(s, num, x + Inches(0.12), y + (RH - Inches(0.62))/2,
       Inches(0.62), Inches(0.62),
       size=22, bold=True, color=WHT, fill=RED, align=PP_ALIGN.CENTER)
    T(s, title, x + Inches(0.88), y + RH*0.22,
      CW2 - Inches(1.0), Inches(0.38),
      size=13, bold=True, color=NAV)
    T(s, desc, x + Inches(0.88), y + RH*0.22 + Inches(0.44),
      CW2 - Inches(1.0), Inches(0.3),
      size=10, color=TXM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S03 업체 개요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "01", "업체 개요", "역삼효태권도장 기본 정보 및 운영 현황")
footer(s, 3)

LW3 = Inches(5.6)
RW3 = W - M*2 - LW3 - IG

# left card – info table
card(s, M, CY, LW3, CH)
clabel(s, "기본 정보", M + Inches(0.14), CY + Inches(0.1))
info = [
    ("명칭",     "역삼효태권도장"),
    ("위치",     "서울 강남구 역삼로 14길 18 2층\n역삼역 3번 출구 858m  ·  역삼초 인근"),
    ("영업시간", "월~금  12:00 – 20:00"),
    ("전화",     "02-552-7582"),
    ("운영인력", "관장 김형열  +  사범  총 2명"),
    ("등록인원", "65명  (유치부 16 · 저학년 23 · 고학년 23 · 중등 3)"),
    ("수강료",   "주 3~4회  월 180,000원  /  주 5회  월 190,000원"),
    ("운영기간", "12년  (인근 3년  +  현 위치 9년)"),
]
row_h = (CH - Inches(0.35)) / len(info)
IY = CY + Inches(0.35)
for lbl, val in info:
    T(s, lbl, M + Inches(0.14), IY + Inches(0.04),
      Inches(1.2), row_h, size=9, bold=True, color=TXL)
    T(s, val, M + Inches(1.38), IY + Inches(0.04),
      LW3 - Inches(1.52), row_h, size=11, color=TXD)
    if lbl != "운영기간":
        div(s, M + Inches(0.14), IY + row_h - Inches(0.02), LW3 - Inches(0.22))
    IY += row_h

# right: 3 stat blocks + bar chart
RX3 = M + LW3 + IG
STAT_H = Inches(1.6)
stats = [("65명","등록 관원"), ("12년","운영 경력"), ("6타임","일일 픽업")]
SH = (STAT_H - IG*2) / 3
SY3 = CY
for val, lbl in stats:
    card(s, RX3, SY3, RW3, SH)
    T(s, val, RX3 + Inches(1.2), SY3 + SH*0.08,
      RW3 - Inches(1.3), SH*0.55,
      size=30, bold=True, color=NAV)
    T(s, lbl, RX3 + Inches(1.2), SY3 + SH*0.65,
      RW3 - Inches(1.3), SH*0.32,
      size=10, color=TXM)
    R(s, RX3 + Inches(0.14), SY3 + SH*0.18,
      Inches(0.04), SH*0.65, fill=RED)
    SY3 += SH + IG

# bar chart card
CHART_H = CB - SY3
card(s, RX3, SY3, RW3, CHART_H)
clabel(s, "관원 구성 현황", RX3 + Inches(0.14), SY3 + Inches(0.1))
members = [
    ("유치부 (7세)",       16, 24.6),
    ("초등 저학년",        23, 35.4),
    ("초등 고학년",        23, 35.4),
    ("중학교",              3,  4.6),
]
bar_total_h = CHART_H - Inches(0.38)
brow_h = bar_total_h / len(members)
BY3 = SY3 + Inches(0.35)
MAX_BW = RW3 - Inches(0.16)
for lbl, cnt, pct in members:
    T(s, lbl, RX3 + Inches(0.14), BY3, Inches(1.82), brow_h*0.45,
      size=9.5, color=TXM)
    R(s, RX3 + Inches(1.98), BY3 + brow_h*0.08,
      MAX_BW - Inches(1.98), brow_h*0.5, fill=BDR)
    bw = (MAX_BW - Inches(1.98)) * cnt / 65
    R(s, RX3 + Inches(1.98), BY3 + brow_h*0.08, bw, brow_h*0.5, fill=NAV)
    T(s, f"{cnt}명  {pct}%",
      RX3 + Inches(1.98) + bw + Inches(0.06), BY3,
      Inches(1.1), brow_h*0.55,
      size=9, bold=True, color=TXD)
    BY3 += brow_h

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S04 현황 진단
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "02", "현황 진단", "온라인 마케팅 인프라 및 강약점 분석")
footer(s, 4)

CALLOUT_H = Inches(0.72)
CHIPS_H   = Inches(0.62)
PROB_H    = CH - CALLOUT_H - CHIPS_H - IG*2
CW4       = (W - M*2 - IG) / 2

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
PX = M
for title, items in problems:
    card(s, PX, CY, CW4, PROB_H)
    clabel(s, "문제 진단", PX + Inches(0.14), CY + Inches(0.1))
    T(s, title, PX + Inches(0.14), CY + Inches(0.35),
      CW4 - Inches(0.22), Inches(0.42),
      size=15, bold=True, color=NAV)
    div(s, PX + Inches(0.14), CY + Inches(0.82), CW4 - Inches(0.22))
    item_h = (PROB_H - Inches(0.98)) / len(items)
    IY4 = CY + Inches(0.94)
    for item in items:
        bullet(s, item, PX + Inches(0.14), IY4, CW4 - Inches(0.22), size=11)
        IY4 += item_h
    PX += CW4 + IG

callout(s, M, CY + PROB_H + IG, W - M*2, CALLOUT_H,
        "오프라인 서비스 품질·학부모 만족도는 매우 높으나, "
        "온라인 검색 결과와 신규 유입 구조로 연결되지 않고 있는 상태",
        label="핵심 진단")

# strength chips
strengths = ["12년 장기 운영 신뢰","역삼초 6타임 무료 픽업",
             "실시간 에듀패밀리 출결","정서적 유대 교육 철학","고학년 40% 유지율"]
SW5 = (W - M*2 - IG*4) / 5
SX5 = M
SY5 = CB - CHIPS_H
for st in strengths:
    TR(s, st, SX5, SY5, SW5, CHIPS_H,
       size=10.5, bold=True, color=NAV,
       fill=WHT, line=BDR, align=PP_ALIGN.CENTER)
    SX5 += SW5 + IG

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S05 4대 핵심 강점  (dark)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
R(s, 0, 0, W, H, fill=NAV)
R(s, 0, 0, Inches(0.1), H, fill=RED)
R(s, 0, H - Inches(0.04), W, Inches(0.04), fill=RED)
OV(s, W - Inches(5), Inches(-1.5), Inches(6.5), Inches(6.5), NAV_DIM)
footer(s, 5)

T(s, "04", M + Inches(0.1), Inches(0.22), Inches(0.6), Inches(0.28),
  size=11, bold=True, color=RED)
T(s, "4대 핵심 강점", M + Inches(0.1), Inches(0.45), Inches(10), Inches(0.82),
  size=38, bold=True, color=WHT)
T(s, "컨설팅 현장 조사를 통해 도출된 역삼효태권도장의 독보적 경쟁력",
  M + Inches(0.1), Inches(1.24), Inches(10), Inches(0.32),
  size=12, color=RGBColor(0x7A, 0x99, 0xCC))
R(s, M + Inches(0.1), Inches(1.56), Inches(0.6), Inches(0.04), fill=RED)

CW5 = (W - M*2 - IG*3) / 4
GY5 = Inches(1.72)
GH5 = H - Inches(0.3) - GY5
GX5 = M

cards_data = [
    ("01","완벽한 케어",
     ["역삼초 6타임 무료 픽업\n(관장 직접 운행, 외주 無)",
      "실시간 에듀패밀리\n출결 사진 전송",
      "맞벌이 학부모 안심\n케어 시스템"]),
    ("02","모두가 주인공",
     ["시범단 위주가 아닌\n전원 성장 수업 구조",
      "예절·체력·태권도·\n생활지도 4축 체계",
      "60분 체계적 수업 설계"]),
    ("03","통합 교육",
     ["기초체력 / 학교체육\n/ 태권도 / 생활지도",
      "정서적 유대 기반\n교육 철학 운영",
      "개인 맞춤 성장 지도"]),
    ("04","12년의 신뢰",
     ["졸업 후에도 찾아오는\n검증된 교육력",
      "고학년·중등 비율 40%\n(장기 신뢰 객관적 증거)",
      "\"가랑비에 옷 젖듯이\"\n서두르지 않는 철학"]),
]

for num, title, buls in cards_data:
    dark_card(s, GX5, GY5, CW5, GH5)
    # large background number
    T(s, num, GX5 + CW5 - Inches(0.9), GY5 + Inches(0.1),
      Inches(0.9), Inches(0.7),
      size=42, bold=True, color=RGBColor(0x1E, 0x3A, 0x6E), align=PP_ALIGN.RIGHT)
    T(s, num, GX5 + Inches(0.16), GY5 + Inches(0.22),
      Inches(0.5), Inches(0.36),
      size=14, bold=True, color=RED)
    T(s, title, GX5 + Inches(0.16), GY5 + Inches(0.62),
      CW5 - Inches(0.28), Inches(0.52),
      size=16, bold=True, color=WHT)
    R(s, GX5 + Inches(0.16), GY5 + Inches(1.2),
      CW5 - Inches(0.28), Inches(0.03),
      fill=RGBColor(0x2A, 0x48, 0x80))
    bY = GY5 + Inches(1.34)
    remaining = GH5 - Inches(1.34)
    bh = remaining / len(buls)
    for b in buls:
        R(s, GX5 + Inches(0.16), bY + Inches(0.08),
          Inches(0.05), Inches(0.05), fill=RED)
        T(s, b, GX5 + Inches(0.3), bY,
          CW5 - Inches(0.4), bh,
          size=10.5, color=RGBColor(0xBB, 0xCC, 0xEE))
        bY += bh
    GX5 += CW5 + IG

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S06 1회차 컨설팅
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "03", "1회차 컨설팅", "2026.05.26  —  브랜드 포지셔닝 및 온라인 전략 수립")
footer(s, 6)

# top positioning strip
POS_H = Inches(0.78)
R(s, M, CY, W - M*2, POS_H, fill=NAV)
R(s, M, CY, Inches(0.055), POS_H, fill=RED)
T(s, "메인 포지셔닝",
  M + Inches(0.14), CY + Inches(0.08), Inches(2), Inches(0.2),
  size=8, bold=True, color=RED)
T(s, "\"아이의 마음까지 책임지는  12년 신뢰\"",
  M + Inches(0.14), CY + Inches(0.3), W - M*2 - Inches(0.22), Inches(0.42),
  size=18, bold=True, color=WHT)

LOWER_Y = CY + POS_H + IG
LOWER_H = CB - LOWER_Y
LW6 = Inches(5.8)
RW6 = W - M*2 - LW6 - IG

# left – brand strategy
card(s, M, LOWER_Y, LW6, LOWER_H)
clabel(s, "브랜드 전략 확정", M + Inches(0.14), LOWER_Y + Inches(0.1))
pos6 = [
    ("핵심 타깃",   "역삼동 맞벌이 학부모 (안심 케어 + 정서적 성장 동시 요구)"),
    ("브랜드 통일", "모든 채널 「역삼효태권도장 / 02-552-7582」 완전 일원화"),
    ("주요 채널",   "네이버 플레이스 최적화  +  인스타그램 주 2회 10분 루틴"),
    ("핵심 메시지", "\"가랑비에 옷 젖듯이\"  서두르지 않는 12년 교육 철학"),
]
row_h6 = (LOWER_H - Inches(0.38)) / len(pos6)
IY6 = LOWER_Y + Inches(0.38)
for lbl, val in pos6:
    T(s, lbl, M + Inches(0.14), IY6 + Inches(0.04),
      Inches(1.3), row_h6*0.4, size=9, bold=True, color=TXL)
    T(s, val, M + Inches(1.52), IY6 + Inches(0.04),
      LW6 - Inches(1.66), row_h6*0.72, size=11.5, color=TXD)
    if lbl != "핵심 메시지":
        div(s, M + Inches(0.14), IY6 + row_h6 - Inches(0.04), LW6 - Inches(0.22))
    IY6 += row_h6

# right – 4 step process
RX6 = M + LW6 + IG
card(s, RX6, LOWER_Y, RW6, LOWER_H)
clabel(s, "1회차 수행 프로세스", RX6 + Inches(0.14), LOWER_Y + Inches(0.1))

steps6 = [
    ("01","온라인 현황 진단",
     "네이버 플레이스 리뷰 현황\n브랜드명 혼재 및 채널 불일치"),
    ("02","교육 철학·핵심 강점 도출",
     "12년 운영 신뢰도\n정서적 유대 기반 교육 정신"),
    ("03","4대 핵심 강점 정의",
     "완벽한 케어 / 모두가 주인공\n통합 교육 / 12년의 신뢰"),
    ("04","브랜드 포지셔닝 확정",
     "메인 포지셔닝 및 타깃 설정\n채널 전략 로드맵 수립·공유"),
]
step_h = (LOWER_H - Inches(0.38)) / len(steps6)
SY6 = LOWER_Y + Inches(0.38)
for num, title, desc in steps6:
    NUM_W = Inches(0.6)
    R(s, RX6 + Inches(0.14), SY6,
      NUM_W, step_h - Inches(0.1), fill=NAV)
    T(s, num, RX6 + Inches(0.14), SY6 + (step_h - Inches(0.1))*0.3,
      NUM_W, Inches(0.38),
      size=14, bold=True, color=RED, align=PP_ALIGN.CENTER)
    R(s, RX6 + Inches(0.14) + NUM_W, SY6,
      RW6 - Inches(0.82), step_h - Inches(0.1),
      fill=STRIPE, line=BDR, lw=Pt(0.5))
    T(s, title, RX6 + Inches(0.88), SY6 + Inches(0.06),
      RW6 - Inches(1.0), Inches(0.32), size=11.5, bold=True, color=NAV)
    T(s, desc, RX6 + Inches(0.88), SY6 + Inches(0.36),
      RW6 - Inches(1.0), step_h - Inches(0.48), size=10, color=TXM)
    SY6 += step_h

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S07 네이버 플레이스 최적화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "04", "네이버 플레이스 전면 최적화", "2회차 컨설팅 2026.05.28  —  검색 최적화 완전 정비")
footer(s, 7)

TIP_H7 = Inches(0.52)
THDR_H = Inches(0.42)
N_ROWS = 5
TROW_H = (CH - THDR_H - TIP_H7 - IG*2) / N_ROWS  # ≈ 0.96"

TC = [M, Inches(2.65), Inches(5.55), Inches(9.62)]
TW = [Inches(2.20), Inches(2.85), Inches(4.02), W - M - Inches(9.62) - Inches(0.08)]

for j,(lbl,cw) in enumerate(zip(["구분","변경 전","변경 후  (최적화 완료)","효과"],TW)):
    TR(s, lbl, TC[j], CY, cw, THDR_H,
       size=11, bold=True, color=WHT,
       fill=RED if j==2 else NAV, align=PP_ALIGN.CENTER)

rows7 = [
    ("공식 상호\n및 번호","상호명·번호 미통일",
     "역삼효태권도장 / 02-552-7582\n완전 통일","검색 정확도↑\n브랜드 신뢰도↑"),
    ("영업 정보\n상태","운영시간 미입력",
     "평일 12:00~20:00 입력\n상담 유도 시간 적용","상담 전환율↑"),
    ("브랜드\n소개글","단순 텍스트 / 매력 미흡",
     "\"가랑비에 옷 젖듯이...\" 12년 철학\n+ 무료픽업 + 출결앱 키워드","감성 신뢰 형성"),
    ("시각 자료\n구성","도장 사진 등록 부족",
     "수련·시설·픽업 사진\n신규 업로드 완료","첫인상 신뢰도↑"),
    ("핵심 서비스\n노출","핵심 강점 기능 미노출",
     "무료픽업·야간수련·에듀패밀리\n안심케어·체력강화 등록","검색 노출↑"),
]
TY7 = CY + THDR_H
for i,(c0,c1,c2,c3) in enumerate(rows7):
    bg7 = WHT if i%2==0 else STRIPE
    for j,(txt7,cw) in enumerate(zip([c0,c1,c2,c3],TW)):
        fc7 = NAV if j==0 else (GRN if j==2 else TXD)
        fw7 = j==0
        R(s, TC[j], TY7, cw, TROW_H,
          fill=GRN_BG if j==2 else bg7, line=BDR, lw=Pt(0.5))
        T(s, txt7, TC[j]+Inches(0.1), TY7+Inches(0.08),
          cw-Inches(0.14), TROW_H-Inches(0.1),
          size=10.5, bold=fw7, color=fc7)
    TY7 += TROW_H

callout(s, M, TY7 + IG, W - M*2, TIP_H7,
        "무료체험 예약 + 네이버 톡톡 기능 추가 → 예비 관원 학부모 소통 편의성 제고 · 전방위 마케팅 활용 가능",
        label="추가 완료")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S08 AI 젬스  (dark)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
R(s, 0, 0, W, H, fill=NAV)
R(s, 0, 0, Inches(0.1), H, fill=RED)
R(s, 0, H - Inches(0.04), W, Inches(0.04), fill=RED)
OV(s, W - Inches(4.5), Inches(-1.2), Inches(5.8), Inches(5.8), NAV_DIM)
footer(s, 8)

T(s, "04", M + Inches(0.1), Inches(0.22), Inches(0.6), Inches(0.28),
  size=11, bold=True, color=RED)
T(s, "AI 젬스  자동화 시스템 구축", M+Inches(0.1), Inches(0.45), Inches(11), Inches(0.78),
  size=34, bold=True, color=WHT)
T(s, "제미나이 젬스(Gemini Gems) 3종 + AI 홍보이미지 → 완전 자립형 마케팅 시스템",
  M+Inches(0.1), Inches(1.22), Inches(11), Inches(0.3),
  size=12, color=RGBColor(0x7A,0x99,0xCC))
R(s, M+Inches(0.1), Inches(1.54), Inches(0.6), Inches(0.04), fill=RED)

GY8 = Inches(1.7)
GH8 = H - Inches(0.3) - GY8
GCW = (W - M*2 - IG*3) / 4
GX8 = M

gems8 = [
    ("GEMS 1","인스타\n포스팅 생성기",
     "사진만 넣으면 인스타 텍스트 + 해시태그 자동 생성",
     "주 2회 포스팅\n5분 이내 완성"),
    ("GEMS 2","리뷰 요청\n카톡 생성기",
     "학부모에게 부담 없는 개인 맞춤 리뷰 요청 메시지 자동 작성",
     "3개월 30개\n달성 핵심 도구"),
    ("GEMS 3","리뷰 답글\n생성기",
     "네이버 플레이스 리뷰 입력 시 전문적인 감사 답글 자동 생성",
     "응답률 100%\n신뢰도 제고"),
    ("AI 이미지","홍보 이미지\n생성",
     "챗GPT·제미나이 활용 아이 초상권 보호 일러스트 제작",
     "홍보물 외주비\n절감"),
]
for badge, title, desc, result in gems8:
    dark_card(s, GX8, GY8, GCW, GH8)
    # badge
    TR(s, badge, GX8, GY8, GCW, Inches(0.48),
       size=12, bold=True, color=WHT,
       fill=RGBColor(0x1A,0x32,0x6A), align=PP_ALIGN.LEFT)
    T(s, badge, GX8+Inches(0.16), GY8+Inches(0.1),
      GCW-Inches(0.24), Inches(0.32), size=12, bold=True, color=RED)
    T(s, title, GX8+Inches(0.16), GY8+Inches(0.6),
      GCW-Inches(0.24), Inches(0.82),
      size=16, bold=True, color=WHT)
    R(s, GX8+Inches(0.16), GY8+Inches(1.52),
      GCW-Inches(0.28), Inches(0.03),
      fill=RGBColor(0x2A,0x48,0x80))
    T(s, desc, GX8+Inches(0.16), GY8+Inches(1.65),
      GCW-Inches(0.24), GH8-Inches(2.75),
      size=11, color=RGBColor(0xBB,0xCC,0xEE))
    # result footer
    R(s, GX8, GY8+GH8-Inches(1.0), GCW, Inches(1.0),
      fill=RGBColor(0x0A,0x14,0x30))
    R(s, GX8, GY8+GH8-Inches(1.0), GCW, Inches(0.04), fill=RED)
    T(s, result, GX8+Inches(0.16), GY8+GH8-Inches(0.9),
      GCW-Inches(0.24), Inches(0.82),
      size=12, bold=True, color=WHT, align=PP_ALIGN.CENTER)
    GX8 += GCW + IG

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S09 관원 구성 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "04", "관원 구성 데이터 분석", "출석부 기반 연령별 분석 → 마케팅 타깃 전략 반영")
footer(s, 9)

LW9 = Inches(7.1)
RW9 = W - M*2 - LW9 - IG

card(s, M, CY, LW9, CH)
clabel(s, "연령별 관원 현황 (총 65명)", M+Inches(0.14), CY+Inches(0.1))

thdrs9 = ["연령대","인원","비율","마케팅 포인트"]
tc9 = [M+Inches(0.14), M+Inches(1.78), M+Inches(2.72), M+Inches(3.52)]
tw9 = [Inches(1.58), Inches(0.9), Inches(0.76), LW9-Inches(3.7)]

THDR9 = Inches(0.32)
T9Y = CY + Inches(0.36)
for j,(lbl,cw) in enumerate(zip(thdrs9,tw9)):
    T(s, lbl, tc9[j], T9Y, cw, THDR9, size=9, bold=True, color=TXL)
div(s, M+Inches(0.14), T9Y+THDR9, LW9-Inches(0.22))

mrows9 = [
    ("7세",          "10명","15.4%","초등 입학 준비 전문성 어필"),
    ("1·2학년",       "12명","18.5%","기초 체력 형성기 집중 케어"),
    ("3학년",        "11명","16.9%","기초 체력 단단한 허리층 타깃"),
    ("4·5·6학년",    "29명","44.6%","학교 체육·교우관계 연계 부각"),
    ("중학교",         "3명", "4.6%","장기 신뢰 극대화 유지 전략"),
    ("합계",         "65명","100%", "역삼동 중심가 안정적 운영 증명"),
]
ROW9 = (CH - Inches(0.36) - THDR9 - Inches(0.06)) / len(mrows9)
T9Y += THDR9 + Inches(0.06)
for i,(age,cnt,pct,tip) in enumerate(mrows9):
    is_last = i==len(mrows9)-1
    bg9 = NAV if is_last else (STRIPE if i%2==0 else WHT)
    for j,(tv,cw) in enumerate(zip([age,cnt,pct,tip],tw9)):
        fc9 = (RED if j==0 and not is_last else
               WHT if is_last else TXD)
        R(s, tc9[j], T9Y, cw, ROW9, fill=bg9,
          line=BDR if not is_last else None, lw=Pt(0.4))
        T(s, tv, tc9[j]+Inches(0.06), T9Y+Inches(0.06),
          cw-Inches(0.08), ROW9-Inches(0.1),
          size=10.5, bold=(j==0 or is_last), color=fc9,
          align=PP_ALIGN.CENTER if j<3 else PP_ALIGN.LEFT)
    T9Y += ROW9

# right – bar chart + insight
RX9 = M + LW9 + IG
card(s, RX9, CY, RW9, CH)
clabel(s, "연령별 비율 시각화", RX9+Inches(0.14), CY+Inches(0.1))

bars9 = [("7세",15.4),("1·2학년",18.5),("3학년",16.9),("4~6학년",44.6),("중학교",4.6)]
INSIGHT_H = Inches(1.9)
BAR_AREA = CH - Inches(0.38) - INSIGHT_H - IG
brow9 = BAR_AREA / len(bars9)
BY9 = CY + Inches(0.38)
MAXBW9 = RW9 - Inches(0.16)
for lbl9, pct9 in bars9:
    T(s, lbl9, RX9+Inches(0.14), BY9+brow9*0.08,
      Inches(1.4), brow9*0.6, size=9.5, color=TXM)
    BW9 = (MAXBW9-Inches(1.5)) * pct9 / 50.0
    R(s, RX9+Inches(1.55), BY9+brow9*0.15, MAXBW9-Inches(1.55), brow9*0.55, fill=BDR)
    R(s, RX9+Inches(1.55), BY9+brow9*0.15, BW9, brow9*0.55, fill=NAV)
    T(s, f"{pct9}%",
      RX9+Inches(1.55)+BW9+Inches(0.06), BY9+brow9*0.08,
      Inches(0.6), brow9*0.6, size=9, bold=True, color=TXD)
    BY9 += brow9

R(s, RX9+Inches(0.14), BY9+IG, RW9-Inches(0.22), INSIGHT_H, fill=NAV)
R(s, RX9+Inches(0.14), BY9+IG, Inches(0.05), INSIGHT_H, fill=RED)
T(s, "고학년 40% 유지율",
  RX9+Inches(0.28), BY9+IG+Inches(0.14),
  RW9-Inches(0.42), Inches(0.36),
  size=13, bold=True, color=RED)
T(s, "일반적으로 학과 공부로 이탈하는 연령대가 전체의 40%를 차지\n→ \"한 번 믿으면 끝까지\" 장기 신뢰 도장의 가장 강력한 객관적 마케팅 근거",
  RX9+Inches(0.28), BY9+IG+Inches(0.58),
  RW9-Inches(0.42), INSIGHT_H-Inches(0.74),
  size=10.5, color=RGBColor(0xBB,0xCC,0xEE))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S10 3회차 컨설팅
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "05", "3회차 컨설팅", "2026.05.29  —  자립 실습 완료 · 리뷰 성장 계획 · 시스템 총정리")
footer(s, 10)

LW10 = Inches(6.0)
RW10 = W - M*2 - LW10 - IG
card(s, M, CY, LW10, CH)
clabel(s, "관장님 자립 실습 완료", M+Inches(0.14), CY+Inches(0.1))
T(s, "5분 루틴 완전 체득 확인",
  M+Inches(0.14), CY+Inches(0.36), LW10-Inches(0.22), Inches(0.38),
  size=14, bold=True, color=NAV)
div(s, M+Inches(0.14), CY+Inches(0.82), LW10-Inches(0.22))

practice10 = [
    ("젬스 3번  리뷰 답글 생성기 활용",
     "네이버 플레이스 기존 리뷰 답글 실제 등록 완료"),
    ("젬스 1번  인스타 포스팅 생성기 활용",
     "인스타그램 2번째 포스팅 업로드 · 품질 조정 완료"),
    ("5분 이내 완성 루틴 완전 체득",
     "사진(1분) → 젬스 문구(2분) → 업로드(2분) = 5분"),
    ("네이버 플레이스 보완 완료",
     "무료체험 예약 + 네이버 톡톡 기능 추가"),
    ("AI 홍보 이미지 생성 실습",
     "챗GPT·제미나이 활용 초상권 보호 일러스트 제작"),
]
pitem_h = (CH - Inches(0.88)) / len(practice10)
PY10 = CY + Inches(0.88)
for title, desc in practice10:
    R(s, M+Inches(0.14), PY10+pitem_h*0.2, Inches(0.12), Inches(0.12), fill=GRN)
    T(s, title, M+Inches(0.36), PY10+Inches(0.04),
      LW10-Inches(0.5), pitem_h*0.45, size=11.5, bold=True, color=TXD)
    T(s, desc, M+Inches(0.36), PY10+pitem_h*0.47,
      LW10-Inches(0.5), pitem_h*0.45, size=10, color=TXM)
    if title != practice10[-1][0]:
        div(s, M+Inches(0.14), PY10+pitem_h-Inches(0.04), LW10-Inches(0.22))
    PY10 += pitem_h

# right – review plan
RX10 = M + LW10 + IG
card(s, RX10, CY, RW10, CH)
clabel(s, "리뷰 30개 달성 실행 계획 (3개월)", RX10+Inches(0.14), CY+Inches(0.1))
T(s, "현재 13개 → 목표 30개",
  RX10+Inches(0.14), CY+Inches(0.36), RW10-Inches(0.22), Inches(0.36),
  size=14, bold=True, color=NAV)

# progress bar
PBAR_Y = CY + Inches(0.86)
R(s, RX10+Inches(0.14), PBAR_Y, RW10-Inches(0.22), Inches(0.42), fill=BDR)
R(s, RX10+Inches(0.14), PBAR_Y, (RW10-Inches(0.22))*13/30, Inches(0.42), fill=NAV)
T(s, "13개", RX10+Inches(0.22), PBAR_Y+Inches(0.1),
  Inches(0.8), Inches(0.24), size=9, bold=True, color=WHT)
T(s, "목표 30개 →",
  RX10+RW10-Inches(1.4), PBAR_Y+Inches(0.1),
  Inches(1.2), Inches(0.24), size=9, color=TXL, align=PP_ALIGN.RIGHT)
div(s, RX10+Inches(0.14), PBAR_Y+Inches(0.5), RW10-Inches(0.22))

timings10 = [
    ("신규 등록 1개월 후", "적응 완료 → 만족도 최고점"),
    ("승급 심사 직후",     "성취감 최고조 → 긍정 리뷰 자연 유도"),
    ("야간수련·이벤트 직후","특별 경험 → 감동 공유 욕구"),
    ("학부모 감사 표현 시", "자발적 만족 → 최적 요청 타이밍"),
]
T(s, "최적 리뷰 요청 타이밍",
  RX10+Inches(0.14), PBAR_Y+Inches(0.6),
  RW10-Inches(0.22), Inches(0.26),
  size=9, bold=True, color=TXL)

titem_h = (CB - PBAR_Y - Inches(0.96)) / len(timings10)
TY10 = PBAR_Y + Inches(0.96)
for timing, reason in timings10:
    R(s, RX10+Inches(0.14), TY10, Inches(0.05), titem_h-Inches(0.08), fill=RED)
    T(s, timing, RX10+Inches(0.32), TY10+Inches(0.04),
      RW10-Inches(0.46), titem_h*0.48, size=11.5, bold=True, color=TXD)
    T(s, reason, RX10+Inches(0.32), TY10+titem_h*0.5,
      RW10-Inches(0.46), titem_h*0.45, size=10, color=TXM)
    if timing != timings10[-1][0]:
        div(s, RX10+Inches(0.14), TY10+titem_h-Inches(0.04), RW10-Inches(0.22))
    TY10 += titem_h

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S11 Before / After
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "06", "컨설팅 성과 비교", "Before → After  전후 비교")
footer(s, 11)

BA_HDR = Inches(0.44)
N_BA = 4
BA_ROW = (CH - BA_HDR - IG*(N_BA-1)) / N_BA
BC = [M, Inches(2.72), Inches(7.34)]
BW = [Inches(2.27), Inches(4.57), W-M-Inches(7.34)-Inches(0.08)]

for j,(lbl,cw,fc,bg11) in enumerate(zip(
    ["항목","BEFORE  컨설팅 이전","AFTER  컨설팅 이후"],
    BW,[WHT,WHT,WHT],
    [NAV,RGBColor(0x8A,0x0E,0x20),GRN])):
    TR(s, lbl, BC[j], CY, cw, BA_HDR,
       size=11, bold=True, color=WHT,
       fill=bg11, align=PP_ALIGN.CENTER)

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
     "마케팅 루틴 전무",
     "주 2회 10분 루틴 확립\n촬영1분+젬스2분+업로드2분"),
]
CUR_Y = CY + BA_HDR
for i,(label,before,after) in enumerate(ba_rows):
    R(s, BC[0], CUR_Y, BW[0], BA_ROW, fill=STRIPE, line=BDR, lw=Pt(0.5))
    T(s, label, BC[0]+Inches(0.1), CUR_Y+(BA_ROW-Inches(0.4))/2,
      BW[0]-Inches(0.15), Inches(0.4),
      size=12, bold=True, color=NAV, align=PP_ALIGN.CENTER)
    R(s, BC[1], CUR_Y, BW[1], BA_ROW, fill=RED_BG, line=BDR, lw=Pt(0.5))
    T(s, before, BC[1]+Inches(0.15), CUR_Y+Inches(0.14),
      BW[1]-Inches(0.22), BA_ROW-Inches(0.2),
      size=11, color=TXD)
    T(s, "→", Inches(6.85), CUR_Y+(BA_ROW-Inches(0.4))/2,
      Inches(0.44), Inches(0.4), size=20, bold=True, color=TXL,
      align=PP_ALIGN.CENTER)
    R(s, BC[2], CUR_Y, BW[2], BA_ROW, fill=GRN_BG, line=BDR, lw=Pt(0.5))
    T(s, after, BC[2]+Inches(0.15), CUR_Y+Inches(0.14),
      BW[2]-Inches(0.22), BA_ROW-Inches(0.2),
      size=11, bold=True, color=GRN)
    if i < N_BA-1:
        CUR_Y += BA_ROW + IG
    else:
        CUR_Y += BA_ROW

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S12 자립형 마케팅 루틴
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "07", "자립형 마케팅 루틴", "주 2회 10분 루틴  —  컨설팅 이후에도 지속 가능한 성장")
footer(s, 12)

FLOW_H  = Inches(2.6)
CALLOUT12_H = Inches(0.56)
CHECKLIST_H = CH - FLOW_H - CALLOUT12_H - IG*2

steps12 = [
    ("01\n사진 촬영","1분","수련 뒷모습\n시설 모습"),
    ("02\n젬스 문구","2분","인스타 텍스트\n해시태그 자동"),
    ("03\n업로드","2분","인스타그램\n포스팅 완성"),
    ("04\n리뷰 요청","수시","젬스 2번 활용\n맞춤 카톡"),
    ("05\n리뷰 답글","즉시","젬스 3번 활용\n자동 생성"),
]
SCW12 = (W - M*2 - IG*4) / 5
SX12 = M
for i,(label,time,desc) in enumerate(steps12):
    card(s, SX12, CY, SCW12, FLOW_H)
    R(s, SX12+Inches(0.055), CY, SCW12-Inches(0.055), Inches(0.44), fill=NAV)
    T(s, time, SX12+Inches(0.16), CY+Inches(0.08),
      SCW12-Inches(0.28), Inches(0.3), size=13, bold=True, color=RED)
    T(s, label, SX12+Inches(0.16), CY+Inches(0.52),
      SCW12-Inches(0.28), Inches(0.76),
      size=13, bold=True, color=NAV)
    div(s, SX12+Inches(0.16), CY+Inches(1.36), SCW12-Inches(0.28))
    for j,line in enumerate(desc.split("\n")):
        T(s, line, SX12+Inches(0.16), CY+Inches(1.5)+j*Inches(0.44),
          SCW12-Inches(0.28), Inches(0.42), size=10.5, color=TXM)
    if i < 4:
        T(s, "›", SX12+SCW12+Inches(0.02), CY+FLOW_H*0.4,
          Inches(0.18), Inches(0.4), size=22, bold=True, color=TXL,
          align=PP_ALIGN.CENTER)
    SX12 += SCW12 + IG

# callout bar
callout(s, M, CY+FLOW_H+IG, W-M*2, CALLOUT12_H,
        "총 5분 이내 완성  —  스마트폰 하나로 전문적인 마케팅 콘텐츠 제작 가능")

# 4 checklist cards
chk12 = [
    ("네이버 플레이스",  ["정보 최신화","리뷰 답글 등록","소식 게시"]),
    ("인스타그램",       ["주 2회 포스팅","해시태그 최적화","팔로워 소통"]),
    ("리뷰 관리",        ["개별 요청 발송","답글 즉시 등록","30개 목표 진행"]),
    ("환경개선",         ["계단·복도 청결","비포·애프터 기록","학부모 첫인상 관리"]),
]
CCW = (W - M*2 - IG*3) / 4
CCX = M
CCY = CY + FLOW_H + IG + CALLOUT12_H + IG
for ctitle, citems in chk12:
    card(s, CCX, CCY, CCW, CHECKLIST_H)
    T(s, ctitle, CCX+Inches(0.16), CCY+Inches(0.12),
      CCW-Inches(0.24), Inches(0.32), size=12, bold=True, color=NAV)
    div(s, CCX+Inches(0.16), CCY+Inches(0.5), CCW-Inches(0.28))
    iitem_h = (CHECKLIST_H - Inches(0.58)) / len(citems)
    IY12 = CCY + Inches(0.58)
    for ci in citems:
        R(s, CCX+Inches(0.16), IY12+iitem_h*0.35, Inches(0.06), Inches(0.06), fill=GRN)
        T(s, ci, CCX+Inches(0.32), IY12+Inches(0.04),
          CCW-Inches(0.44), iitem_h*0.75, size=10.5, color=TXD)
        IY12 += iitem_h
    CCX += CCW + IG

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S13 자립 시스템 총정리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "05", "자립 시스템 총정리", "컨설팅 종료 시점 구축 완료 현황")
footer(s, 13)

items13 = [
    ("네이버 플레이스 최적화 및 업데이트",
     "브랜드 통일·운영시간·소개글·사진·핵심 서비스 전면 정비 / 무료체험 예약 + 네이버 톡톡 추가"),
    ("인스타그램 공식 채널 정상 가동",
     "역삼효태권도장 공식 인스타그램 개설·프로필 구성·첫 포스팅 완료 / 관장님 직접 실습으로 지속 운영 역량 확보"),
    ("AI 젬스 4종 완전 체득 및 실습 완료",
     "인스타 포스팅 생성기 / 리뷰 요청 카톡 생성기 / 리뷰 답글 생성기 / AI 홍보이미지 생성 → 매뉴얼 제작 및 숙지 확인"),
    ("주 2회 10분 마케팅 루틴 확립",
     "사진(1분) + 젬스(2분) + 업로드(2분) = 5분 루틴 / 외부 대행 없이 스스로 운영 가능한 자립형 마케팅 시스템"),
    ("리뷰 30개 달성 단계별 실행 계획 수립",
     "현재 13개 → 3개월 내 30개 목표 / 최적 타이밍별 요청 전략 확정 / 젬스 2번 개별 맞춤 발송으로 자연스러운 리뷰 확보"),
    ("환경개선 및 학부모 눈높이 소통 의지 제고",
     "계단·복도 청결 환경개선 (첫인상 관리) / 서울시 소상공인 지원사업 연계 시설개선 최대 300만원 지원 안내"),
]
ITEM_H = (CH - IG*5) / 6
IY13 = CY
for title, desc in items13:
    R(s, M, IY13, W-M*2, ITEM_H, fill=WHT, line=BDR, lw=Pt(0.75))
    R(s, M, IY13, Inches(0.055), ITEM_H, fill=RED)
    TR(s, "✓", M+Inches(0.1), IY13+(ITEM_H-Inches(0.52))/2,
       Inches(0.5), Inches(0.52),
       size=16, bold=True, color=WHT, fill=GRN, align=PP_ALIGN.CENTER)
    T(s, title, M+Inches(0.74), IY13+Inches(0.08),
      Inches(5.5), Inches(0.34), size=12.5, bold=True, color=NAV)
    T(s, desc, M+Inches(0.74), IY13+Inches(0.42),
      W-M*2-Inches(0.86), ITEM_H-Inches(0.5),
      size=10, color=TXM)
    IY13 += ITEM_H + IG

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S14 향후 제언
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
page_bg(s)
header(s, "08", "향후 제언", "지속 가능성 및 성장 전략 제언")
footer(s, 14)

QUOTE_H = Inches(0.9)
CARD_H14 = (CH - QUOTE_H - IG*3) / 2

recs14 = [
    ("01","단톡방 유지 사후 관리",
     "컨설팅 팀과 단체 채팅방 유지로 추후 궁금증 즉시 해결\n지속적인 관리 및 피드백 제공 예정"),
    ("02","WOM 입소문 마케팅",
     "컨설팅 수혜 업체가 주변 소상공인 대상으로 홍보\n→ 추천제도 운영으로 선순환 생태계 구축 제언"),
    ("03","서울시 지원사업 연계",
     "서울특별시 소상공인 지원사업 활용 (seoulsbdc.or.kr)\n하반기 시설개선 최대 300만원 지원 활용 제언"),
    ("04","콘텐츠 자산 지속 축적",
     "수련 사진·영상 꾸준한 기록 → 인스타·네이버 자산화\n\"가랑비에 옷 젖듯이\" 철학을 온라인에서도 실현"),
]
R14CW = (W - M*2 - IG) / 2
for i,(num,title,desc) in enumerate(recs14):
    CX14 = M if i%2==0 else M+R14CW+IG
    CY14 = CY if i<2 else CY+CARD_H14+IG
    card(s, CX14, CY14, R14CW, CARD_H14)
    T(s, num, CX14+Inches(0.16), CY14+Inches(0.14),
      Inches(0.5), Inches(0.5), size=22, bold=True, color=RED)
    T(s, title, CX14+Inches(0.66), CY14+Inches(0.18),
      R14CW-Inches(0.8), Inches(0.36), size=14, bold=True, color=NAV)
    div(s, CX14+Inches(0.16), CY14+Inches(0.6), R14CW-Inches(0.28))
    for j,line in enumerate(desc.split("\n")):
        T(s, line, CX14+Inches(0.16), CY14+Inches(0.74)+j*Inches(0.38),
          R14CW-Inches(0.28), Inches(0.36), size=11, color=TXD)

# quote
QY = CB - QUOTE_H
R(s, M, QY, W-M*2, QUOTE_H, fill=NAV)
R(s, M, QY, Inches(0.055), QUOTE_H, fill=RED)
T(s, "관장님 소회", M+Inches(0.18), QY+Inches(0.1), Inches(1.5), Inches(0.2),
  size=8, bold=True, color=RED)
T(s, "\"태권도 학원들이 대체로 홍보 마케팅과 거리가 멀었는데, "
     "3일 동안 완전히! 꼭 필요한 것을 너무나도 꽉꽉 채워주셨습니다.  감사합니다!\"",
  M+Inches(0.18), QY+Inches(0.28), W-M*2-Inches(0.26), Inches(0.54),
  size=12.5, bold=True, color=WHT)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S15 CLOSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = sl()
R(s, 0, 0, W, H, fill=NAV)
R(s, 0, 0, Inches(0.1), H, fill=RED)
R(s, 0, H-Inches(0.06), W, Inches(0.06), fill=RED)
OV(s, W-Inches(6.0), Inches(-2.2), Inches(8), Inches(8), NAV_DIM)
OV(s, W-Inches(2.5), H-Inches(4.0), Inches(5), Inches(5),
   RGBColor(0x08,0x10,0x24))

# left content
T(s, "감사합니다", M+Inches(0.1), Inches(1.3), Inches(9), Inches(1.5),
  size=68, bold=True, color=WHT)
R(s, M+Inches(0.1), Inches(2.9), Inches(0.8), Inches(0.04), fill=RED)
T(s, "역삼효태권도장  온라인 마케팅 컨설팅 보고서",
  M+Inches(0.1), Inches(3.06), Inches(9), Inches(0.44),
  size=15, color=RGBColor(0x7A,0x99,0xCC))

summary15 = [
    "네이버 플레이스 완전 최적화 및 브랜드 통일",
    "인스타그램 공식 채널 개설 및 첫 포스팅 완료",
    "AI 젬스 3종 자동화 시스템 완전 체득",
    "주 2회 10분 마케팅 루틴 자립 시스템 완성",
    "3개월 리뷰 30개 달성 단계별 실행 계획 수립",
]
SY15 = Inches(3.72)
for pt in summary15:
    R(s, M+Inches(0.1), SY15+Inches(0.11), Inches(0.04), Inches(0.12), fill=RED)
    T(s, pt, M+Inches(0.28), SY15, Inches(7.5), Inches(0.36),
      size=12, color=RGBColor(0xBB,0xCC,0xEE))
    SY15 += Inches(0.44)

# team info box
R(s, M+Inches(0.1), H-Inches(1.28), Inches(7), Inches(0.72),
  fill=NAV_LT, line=RGBColor(0x28,0x48,0x80))
R(s, M+Inches(0.1), H-Inches(1.28), Inches(0.055), Inches(0.72), fill=RED)
T(s, "컨설팅 팀", M+Inches(0.24), H-Inches(1.22),
  Inches(1.2), Inches(0.22), size=8, bold=True, color=RED)
T(s, "B그룹 5조  권용준 · 손미현  |  2026.05.26 – 2026.05.29",
  M+Inches(0.24), H-Inches(1.0), Inches(6.6), Inches(0.36),
  size=11, color=RGBColor(0xCC,0xD8,0xEE))

OUT = "/home/user/-/역삼효태권도장_온라인마케팅컨설팅_보고서.pptx"
prs.save(OUT)
print("Saved:", OUT)
