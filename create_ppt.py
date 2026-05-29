from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from pptx.enum.dml import MSO_THEME_COLOR
import pptx.oxml.ns as nsmap
from lxml import etree
from pptx.oxml.ns import qn
import copy

# ─── Color Palette ─────────────────────────────────────────────────────────────
C_NAVY      = RGBColor(0x0D, 0x1B, 0x3E)   # deep navy (primary bg)
C_RED       = RGBColor(0xC0, 0x1C, 0x2C)   # taekwondo red
C_GOLD      = RGBColor(0xF5, 0xA6, 0x23)   # warm gold accent
C_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
C_LIGHT     = RGBColor(0xF0, 0xF4, 0xFA)   # very light blue-grey
C_MID       = RGBColor(0x4A, 0x6B, 0x9A)   # mid-blue
C_DARK_TEXT = RGBColor(0x1A, 0x1A, 0x2E)
C_GREEN     = RGBColor(0x16, 0xA0, 0x85)   # success green
C_ORANGE    = RGBColor(0xE6, 0x7E, 0x22)
C_GREY      = RGBColor(0x7F, 0x8C, 0x8D)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]  # completely blank

# ─── Helper functions ───────────────────────────────────────────────────────────

def add_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_width=None):
    shape = slide.shapes.add_shape(1, left, top, width, height)  # MSO_SHAPE_TYPE.RECTANGLE
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        if line_width:
            shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape

def add_text(slide, text, left, top, width, height,
             font_size=18, bold=False, color=C_WHITE,
             align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf    = txBox.text_frame
    tf.word_wrap = wrap
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(font_size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return txBox

def add_text_box(slide, text, left, top, width, height,
                 font_size=18, bold=False, color=C_WHITE,
                 align=PP_ALIGN.LEFT, italic=False,
                 bg_color=None, border_color=None, padding=None):
    """Rectangle with centered text inside."""
    rect = add_rect(slide, left, top, width, height,
                    fill_color=bg_color, line_color=border_color)
    tf = rect.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(font_size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return rect

def header_band(slide, title, subtitle=None,
                bg=C_NAVY, accent=C_RED, height=Inches(1.4)):
    """Full-width header band with optional accent bar."""
    add_rect(slide, 0, 0, SLIDE_W, height, fill_color=bg)
    # accent left bar
    add_rect(slide, 0, 0, Inches(0.18), height, fill_color=accent)
    # title
    add_text(slide, title, Inches(0.4), Inches(0.22), Inches(9), Inches(0.7),
             font_size=32, bold=True, color=C_WHITE)
    if subtitle:
        add_text(slide, subtitle, Inches(0.4), Inches(0.88), Inches(12), Inches(0.42),
                 font_size=15, bold=False, color=RGBColor(0xBB, 0xCC, 0xEE))

def footer_band(slide, text="역삼효태권도장 | 소상공인 온라인 마케팅 컨설팅 보고서 | 2026.05"):
    add_rect(slide, 0, SLIDE_H - Inches(0.35), SLIDE_W, Inches(0.35),
             fill_color=C_NAVY)
    add_text(slide, text, Inches(0.3), SLIDE_H - Inches(0.32), Inches(12), Inches(0.3),
             font_size=9, color=RGBColor(0x88, 0x99, 0xBB))

def slide_number(slide, n):
    add_text(slide, str(n), SLIDE_W - Inches(0.5), SLIDE_H - Inches(0.33),
             Inches(0.4), Inches(0.28), font_size=9,
             color=RGBColor(0xAA, 0xBB, 0xCC), align=PP_ALIGN.RIGHT)

# ─── Slide factory ─────────────────────────────────────────────────────────────

def new_slide():
    return prs.slides.add_slide(BLANK)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 1 – COVER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
# Full navy background
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_NAVY)
# Red accent stripe (left)
add_rect(s, 0, 0, Inches(0.55), SLIDE_H, fill_color=C_RED)
# Gold diagonal accent band
add_rect(s, Inches(0.55), Inches(4.8), SLIDE_W, Inches(0.07), fill_color=C_GOLD)

# Large decorative circle (top-right watermark)
circle = s.shapes.add_shape(9, SLIDE_W - Inches(3.8), Inches(-1.2), Inches(5), Inches(5))  # oval
circle.fill.solid(); circle.fill.fore_color.rgb = RGBColor(0x14, 0x28, 0x55)
circle.line.fill.background()

# Badge box
add_rect(s, Inches(0.9), Inches(1.1), Inches(3.2), Inches(0.55),
         fill_color=C_RED)
add_text(s, "소상공인 컨설팅 보고서", Inches(0.92), Inches(1.12),
         Inches(3.2), Inches(0.52), font_size=14, bold=True, color=C_WHITE)

# Main title
add_text(s, "역삼효태권도장", Inches(0.9), Inches(1.85), Inches(9), Inches(1.1),
         font_size=54, bold=True, color=C_WHITE)
add_text(s, "온라인 마케팅 진단 및 자립형 마케팅 시스템 구축", Inches(0.9), Inches(2.95),
         Inches(10), Inches(0.65), font_size=22, bold=False,
         color=RGBColor(0xBB, 0xCC, 0xEE))

# Divider
add_rect(s, Inches(0.9), Inches(3.7), Inches(5), Inches(0.05), fill_color=C_GOLD)

# Meta info
meta = [
    ("업체명",    "역삼효태권도장"),
    ("대표",      "김형열 관장"),
    ("컨설팅팀",  "B그룹 5조 | 권용준, 손미현"),
    ("기간",      "2026.05.26 ~ 2026.05.29  (총 3일)"),
    ("분야",      "학원업 | 온라인 마케팅 진단 및 솔루션"),
]
y = Inches(3.9)
for label, val in meta:
    add_text(s, f"{label}", Inches(0.9), y, Inches(1.5), Inches(0.35),
             font_size=11, color=C_GOLD, bold=True)
    add_text(s, val, Inches(2.3), y, Inches(7), Inches(0.35),
             font_size=11, color=C_WHITE)
    y += Inches(0.38)

slide_number(s, 1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 2 – TABLE OF CONTENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "목차  Contents", "역삼효태권도장 소상공인 컨설팅 보고서")
footer_band(s); slide_number(s, 2)

toc_items = [
    ("01", "업체 개요",              "역삼효태권도장 기본 정보 및 운영 현황"),
    ("02", "현황 진단 & 핵심 강점",  "온라인 마케팅 현황 분석 및 4대 강점 도출"),
    ("03", "1회차 컨설팅",           "브랜드 포지셔닝 · 네이버 플레이스 전략 수립"),
    ("04", "2회차 컨설팅",           "네이버 플레이스 최적화 · AI 젬스 시스템 구축"),
    ("05", "3회차 컨설팅",           "자립 실습 완료 · 리뷰 성장 계획 · 시스템 총정리"),
    ("06", "컨설팅 성과 비교",       "Before → After 전후 비교"),
    ("07", "자립형 마케팅 루틴",     "주 2회 10분 루틴 및 실행 로드맵"),
    ("08", "향후 제언",              "지속가능성 및 성장 전략 제언"),
]

cols  = 2
gap   = Inches(0.25)
col_w = (SLIDE_W - Inches(0.8) - gap) / 2
row_h = Inches(0.68)
start_y = Inches(1.55)

colors_num = [C_RED, C_GOLD, C_MID, C_GREEN, C_ORANGE, C_RED, C_MID, C_GREEN]

for i, (num, title, desc) in enumerate(toc_items):
    col = i % 2
    row = i // 2
    x = Inches(0.4) + col * (col_w + gap)
    y = start_y + row * (row_h + Inches(0.1))

    # card bg
    add_rect(s, x, y, col_w, row_h, fill_color=C_WHITE,
             line_color=RGBColor(0xDD, 0xE5, 0xF0), line_width=Pt(0.75))
    # number pill
    add_rect(s, x, y, Inches(0.58), row_h, fill_color=colors_num[i])
    add_text(s, num, x + Inches(0.01), y + Inches(0.14),
             Inches(0.56), Inches(0.4), font_size=18, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)
    # title
    add_text(s, title, x + Inches(0.66), y + Inches(0.06),
             col_w - Inches(0.76), Inches(0.35),
             font_size=14, bold=True, color=C_DARK_TEXT)
    # desc
    add_text(s, desc, x + Inches(0.66), y + Inches(0.36),
             col_w - Inches(0.76), Inches(0.28),
             font_size=10, color=C_GREY)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 3 – 업체 개요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "01  업체 개요", "역삼효태권도장 기본 정보 및 운영 현황")
footer_band(s); slide_number(s, 3)

# Left info card
cw = Inches(6.0)
ch = SLIDE_H - Inches(2.0)
add_rect(s, Inches(0.4), Inches(1.6), cw, ch, fill_color=C_WHITE,
         line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(1))

info_rows = [
    ("🏫  명칭",    "역삼효태권도장"),
    ("📍  위치",    "서울 강남구 역삼로 14길 18 2층\n(역삼역 3번 출구 858m / 역삼초 인근)"),
    ("🕐  영업시간","월~금  12:00 ~ 20:00"),
    ("📞  전화",    "02-552-7582"),
    ("👤  운영인력","관장(김형열) + 사범 총 2명"),
    ("🥋  등록인원","65명\n유치부 16명 | 초등저학년 23명 | 초등고학년 23명 | 중학교 3명"),
    ("💰  수강료",  "주 3~4회: 월 180,000원\n주 5회: 월 190,000원"),
    ("📅  운영기간","12년 (인근 3년 + 현 위치 9년)"),
]

iy = Inches(1.75)
for label, val in info_rows:
    add_text(s, label, Inches(0.55), iy, Inches(1.65), Inches(0.42),
             font_size=10.5, bold=True, color=C_MID)
    add_text(s, val,   Inches(2.25), iy, Inches(4.0),  Inches(0.42),
             font_size=10.5, color=C_DARK_TEXT)
    add_rect(s, Inches(0.55), iy + Inches(0.38), Inches(5.7), Inches(0.008),
             fill_color=RGBColor(0xE8, 0xED, 0xF5))
    iy += Inches(0.45)

# Right stats panel
rx = Inches(6.8)
ry = Inches(1.6)
rw = Inches(6.1)
add_rect(s, rx, ry, rw, Inches(1.1), fill_color=C_NAVY)
add_text(s, "관원 구성 현황 (총 65명)", rx + Inches(0.2), ry + Inches(0.3),
         rw - Inches(0.3), Inches(0.5), font_size=16, bold=True, color=C_WHITE)

member_data = [
    ("유치부 (7세)",       16, "15.4%+\n(10명 만 7세)", C_GOLD),
    ("초등 저학년 (1~3학년)", 23, "35.4%", C_MID),
    ("초등 고학년 (4~6학년)", 23, "35.4%", C_GREEN),
    ("중학교",               3, "4.6%", C_ORANGE),
]

bar_total = 65
bx = rx + Inches(0.2)
by = ry + Inches(1.2)
bar_max_w = rw - Inches(0.4)

for label, cnt, pct_str, color in member_data:
    bar_w = bar_max_w * cnt / bar_total
    add_rect(s, bx, by, bar_max_w, Inches(0.44), fill_color=RGBColor(0xE8, 0xED, 0xF5))
    add_rect(s, bx, by, bar_w, Inches(0.44), fill_color=color)
    add_text(s, f"{label}  {cnt}명", bx + Inches(0.08), by + Inches(0.06),
             bar_max_w - Inches(0.1), Inches(0.34), font_size=10.5,
             bold=True, color=C_WHITE if cnt > 10 else C_DARK_TEXT)
    by += Inches(0.54)

# Insight box
by += Inches(0.1)
add_rect(s, rx, by, rw, Inches(0.85), fill_color=RGBColor(0x1A, 0x52, 0x76))
add_text(s, "☞  고학년 + 중학생 비중 40% → \"한 번 믿으면 끝까지\"  장기 신뢰 도장",
         rx + Inches(0.2), by + Inches(0.15), rw - Inches(0.3), Inches(0.6),
         font_size=11.5, bold=True, color=C_GOLD)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 4 – 현황 진단
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "02  현황 진단", "온라인 마케팅 인프라 및 강약점 분석")
footer_band(s); slide_number(s, 4)

# Two problem cards
problems = [
    ("마케팅 인프라 부족", C_RED,
     ["네이버 플레이스 리뷰 13개(기본 4 / 키워드 7 / 블로그 2)",
      "브랜드명 혼재 (역삼효태권도장 / 효태권도 등)",
      "채널별 정보 불일치 → 검색 신뢰도 분산",
      "신규 고객 유입 구조 미흡"]),
    ("디지털 활용 역량 저하", C_ORANGE,
     ["인스타그램 등 SNS 채널 업데이트 미흡",
      "홍보 콘텐츠 제작 경험 부족",
      "학부모 디지털 소통 루틴 부재",
      "마케팅 루틴 전무"]),
]

px = Inches(0.4)
for i, (title, col, items) in enumerate(problems):
    pw = Inches(5.9)
    py = Inches(1.6)
    ph = Inches(2.7)
    add_rect(s, px, py, pw, Inches(0.5), fill_color=col)
    add_text(s, f"⚠  {title}", px + Inches(0.1), py + Inches(0.06),
             pw - Inches(0.2), Inches(0.42), font_size=15, bold=True, color=C_WHITE)
    add_rect(s, px, py + Inches(0.5), pw, ph - Inches(0.5),
             fill_color=C_WHITE, line_color=col, line_width=Pt(1.5))
    iy = py + Inches(0.65)
    for item in items:
        add_rect(s, px + Inches(0.15), iy + Inches(0.05),
                 Inches(0.06), Inches(0.28), fill_color=col)
        add_text(s, item, px + Inches(0.3), iy, pw - Inches(0.4), Inches(0.38),
                 font_size=11.5, color=C_DARK_TEXT)
        iy += Inches(0.45)
    px += Inches(6.2)

# Core diagnosis result
add_rect(s, Inches(0.4), Inches(4.45), SLIDE_W - Inches(0.8), Inches(0.85),
         fill_color=C_NAVY)
add_text(s, "☞  핵심 진단: 오프라인 서비스 품질·학부모 만족도는 매우 높으나,\n"
            "온라인 검색 결과와 신규 유입 구조로 연결되지 않고 있는 상태",
         Inches(0.6), Inches(4.52), SLIDE_W - Inches(1.2), Inches(0.75),
         font_size=12.5, bold=True, color=C_GOLD)

# Strengths header
add_rect(s, Inches(0.4), Inches(5.42), SLIDE_W - Inches(0.8), Inches(0.45),
         fill_color=C_MID)
add_text(s, "✅  현장 조사로 확인된 실질 강점", Inches(0.6), Inches(5.45),
         Inches(6), Inches(0.38), font_size=13, bold=True, color=C_WHITE)

strengths = [
    "12년 장기 운영 신뢰도",
    "역삼초 6타임 무료 픽업",
    "실시간 에듀패밀리 출결 사진 전송",
    "정서적 유대 교육 철학",
    "고학년·중등 40% 유지율",
]
sx = Inches(0.4)
for st in strengths:
    sw = Inches(2.34)
    add_rect(s, sx, Inches(5.97), sw, Inches(0.72),
             fill_color=C_WHITE, line_color=C_MID, line_width=Pt(1))
    add_text(s, st, sx + Inches(0.1), Inches(6.02), sw - Inches(0.15), Inches(0.65),
             font_size=10, bold=True, color=C_DARK_TEXT, align=PP_ALIGN.CENTER)
    sx += sw + Inches(0.18)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 5 – 4대 핵심 강점 (visual)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_NAVY)
add_rect(s, 0, 0, Inches(0.18), SLIDE_H, fill_color=C_RED)
footer_band(s); slide_number(s, 5)

add_text(s, "역삼효태권도장  4대 핵심 강점", Inches(0.4), Inches(0.2),
         Inches(10), Inches(0.65), font_size=30, bold=True, color=C_WHITE)
add_text(s, "컨설팅 현장 조사를 통해 도출된 핵심 경쟁력",
         Inches(0.4), Inches(0.82), Inches(10), Inches(0.38),
         font_size=14, color=RGBColor(0xBB, 0xCC, 0xEE))
add_rect(s, Inches(0.4), Inches(1.22), Inches(4.5), Inches(0.04), fill_color=C_GOLD)

cards = [
    ("01", "완벽한 케어",
     "역삼초 6타임 무료 픽업 (직접 운행)\n실시간 에듀패밀리 출결 사진 전송\n외주 기사 없는 관장 직접 책임제",
     C_RED),
    ("02", "모두가 주인공",
     "시범단 위주 아닌 전원 성장 수업 구조\n예절·체력·태권도·생활지도 4축 시스템\n60분 체계적 수업 설계",
     C_GOLD),
    ("03", "통합 교육",
     "기초체력 / 학교체육 / 태권도 실기\n생활지도 통합 60분 수업 구조\n정서적 유대 기반 교육 철학",
     C_GREEN),
    ("04", "12년의 신뢰",
     "졸업생이 찾아오고 이사 후에도 다니는\n검증된 교육력 (고학년·중등 40% 유지)\n\"가랑비에 옷 젖듯이\" 서두르지 않는 방식",
     C_MID),
]

cw = (SLIDE_W - Inches(0.8) - Inches(0.3) * 3) / 4
cy = Inches(1.5)
ch = Inches(5.5)
cx = Inches(0.4)

for num, title, desc, color in cards:
    add_rect(s, cx, cy, cw, ch, fill_color=RGBColor(0x14, 0x28, 0x55),
             line_color=color, line_width=Pt(1.5))
    # top color strip
    add_rect(s, cx, cy, cw, Inches(0.55), fill_color=color)
    add_text(s, num, cx + Inches(0.1), cy + Inches(0.06),
             cw - Inches(0.2), Inches(0.44), font_size=22, bold=True,
             color=C_WHITE, align=PP_ALIGN.LEFT)
    add_text(s, title, cx + Inches(0.12), cy + Inches(0.65),
             cw - Inches(0.2), Inches(0.55), font_size=16, bold=True,
             color=color)
    # description lines
    ty = cy + Inches(1.3)
    for line in desc.split("\n"):
        add_text(s, f"• {line}", cx + Inches(0.12), ty,
                 cw - Inches(0.2), Inches(0.48), font_size=11,
                 color=RGBColor(0xCC, 0xDD, 0xFF))
        ty += Inches(0.45)

    cx += cw + Inches(0.3)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 6 – 브랜드 포지셔닝 & 타깃 전략 (1회차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "03  1회차 컨설팅", "2026.05.26 | 브랜드 포지셔닝 및 온라인 전략 수립")
footer_band(s); slide_number(s, 6)

# Left – positioning card
lw = Inches(5.8)
add_rect(s, Inches(0.4), Inches(1.6), lw, Inches(5.55),
         fill_color=C_WHITE, line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(1))

add_rect(s, Inches(0.4), Inches(1.6), lw, Inches(0.5), fill_color=C_NAVY)
add_text(s, "브랜드 포지셔닝 확정", Inches(0.6), Inches(1.65),
         lw - Inches(0.2), Inches(0.42), font_size=15, bold=True, color=C_WHITE)

# Positioning statement highlight
add_rect(s, Inches(0.55), Inches(2.25), lw - Inches(0.25), Inches(0.85),
         fill_color=RGBColor(0xFD, 0xF3, 0xE0))
add_text(s, "\"아이의 마음까지 책임지는  12년 신뢰\"",
         Inches(0.65), Inches(2.33), lw - Inches(0.4), Inches(0.7),
         font_size=16, bold=True, color=C_RED, align=PP_ALIGN.CENTER)

pos_items = [
    ("핵심 타깃",  "역삼동 맞벌이 학부모\n(안심 케어 + 정서적 성장 동시 필요 계층)"),
    ("브랜드 통일", "모든 채널 '역삼효태권도장 / 02-552-7582' 일원화"),
    ("주요 채널",  "네이버 플레이스 최적화 + 인스타그램 10분 루틴"),
    ("핵심 메시지","\"가랑비에 옷 젖듯이\" 서두르지 않는 12년 교육철학"),
]
py2 = Inches(3.25)
for label, val in pos_items:
    add_text(s, label, Inches(0.6), py2, Inches(1.6), Inches(0.45),
             font_size=10.5, bold=True, color=C_MID)
    add_text(s, val, Inches(2.2), py2, Inches(3.8), Inches(0.45),
             font_size=10.5, color=C_DARK_TEXT)
    add_rect(s, Inches(0.6), py2 + Inches(0.4), lw - Inches(0.35), Inches(0.008),
             fill_color=RGBColor(0xE0, 0xE8, 0xF5))
    py2 += Inches(0.52)

# Right – consulting flow
rx = Inches(6.55)
rw = Inches(6.4)
add_rect(s, rx, Inches(1.6), rw, Inches(0.5), fill_color=C_MID)
add_text(s, "1회차 수행 프로세스", rx + Inches(0.15), Inches(1.65),
         rw - Inches(0.2), Inches(0.42), font_size=15, bold=True, color=C_WHITE)

steps = [
    (C_RED,   "STEP 1", "온라인 현황 진단",
     "네이버 플레이스 리뷰 현황\n브랜드명 혼재 및 채널 불일치 확인"),
    (C_GOLD,  "STEP 2", "교육 철학 · 핵심 강점 도출",
     "총 12년 운영 신뢰도\n정서적 유대 기반 교육 정신 파악"),
    (C_GREEN, "STEP 3", "4대 핵심 강점 정의",
     "완벽한 케어 / 모두가 주인공\n통합 교육 / 12년의 신뢰"),
    (C_MID,   "STEP 4", "브랜드 포지셔닝 확정",
     "메인 포지셔닝 및 타깃 설정\n채널 전략 로드맵 공유"),
]

sy = Inches(2.25)
for color, step, title, desc in steps:
    add_rect(s, rx, sy, Inches(0.8), Inches(0.95), fill_color=color)
    add_text(s, step, rx + Inches(0.02), sy + Inches(0.2),
             Inches(0.76), Inches(0.6), font_size=9.5, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)
    add_rect(s, rx + Inches(0.8), sy, rw - Inches(0.8), Inches(0.95),
             fill_color=C_WHITE, line_color=color, line_width=Pt(1))
    add_text(s, title, rx + Inches(0.92), sy + Inches(0.04),
             rw - Inches(1.0), Inches(0.38), font_size=12.5, bold=True,
             color=color)
    add_text(s, desc, rx + Inches(0.92), sy + Inches(0.38),
             rw - Inches(1.0), Inches(0.52), font_size=10, color=C_DARK_TEXT)
    # arrow
    if step != "STEP 4":
        add_rect(s, rx + Inches(0.3), sy + Inches(0.95),
                 Inches(0.2), Inches(0.12), fill_color=color)
    sy += Inches(1.07)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 7 – 네이버 플레이스 최적화 (2회차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "04  네이버 플레이스 전면 최적화", "2회차 컨설팅 2026.05.28 | 검색 최적화 완전 정비")
footer_band(s); slide_number(s, 7)

# Table header
cols_x = [Inches(0.4), Inches(2.7), Inches(5.2), Inches(9.2)]
col_labels = ["구분", "변경 전", "변경 후 (최적화 완료)", "효과"]
col_widths = [Inches(2.28), Inches(2.45), Inches(3.95), Inches(3.55)]

ty = Inches(1.6)
th = Inches(0.45)
for i, label in enumerate(col_labels):
    add_rect(s, cols_x[i], ty, col_widths[i], th,
             fill_color=C_NAVY)
    add_text(s, label, cols_x[i] + Inches(0.08), ty + Inches(0.06),
             col_widths[i] - Inches(0.1), Inches(0.38),
             font_size=12, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

table_rows = [
    ("공식 상호 및 번호",
     "상호명/대표번호 미통일",
     "역삼효태권도장 / 02-552-7582\n완전 통일",
     "검색 정확도↑\n브랜드 신뢰도↑"),
    ("영업 정보 상태",
     "운영시간 미입력",
     "평일 12:00~20:00 적용\n정확한 상담 유도 시간 입력",
     "상담 전환율↑"),
    ("브랜드 소개글",
     "단순 텍스트 / 매력 미흡",
     "\"가랑비에 옷 젖듯이...\"\n12년 철학 + 무료픽업 + 출결앱 키워드",
     "감성적 신뢰 형성"),
    ("시각 자료 구성",
     "도장 관련 사진 등록 부족",
     "수련 모습·쾌적한 시설·\n안전 픽업 사진 신규 업로드",
     "첫인상 신뢰도↑"),
    ("핵심 서비스 노출",
     "핵심 강점 기능 미노출",
     "무료픽업·야간수련·에듀패밀리\n안심케어·장기수련생·체력강화 등록",
     "검색 노출 키워드↑"),
]

row_colors = [C_WHITE, RGBColor(0xF5, 0xF8, 0xFF), C_WHITE,
              RGBColor(0xF5, 0xF8, 0xFF), C_WHITE]
ty += th

for i, (col0, col1, col2, col3) in enumerate(table_rows):
    rh = Inches(0.75)
    bg = row_colors[i]
    for j, (txt, cw) in enumerate(zip([col0, col1, col2, col3], col_widths)):
        fc = C_RED if j == 0 else (C_GREEN if j == 2 else C_DARK_TEXT)
        fw = True if j == 0 else False
        add_rect(s, cols_x[j], ty, cw, rh, fill_color=bg,
                 line_color=RGBColor(0xD0, 0xDA, 0xEC), line_width=Pt(0.5))
        add_text(s, txt, cols_x[j] + Inches(0.08), ty + Inches(0.05),
                 cw - Inches(0.12), rh - Inches(0.08),
                 font_size=10, bold=fw, color=fc)
    ty += rh

# Bottom tip
add_rect(s, Inches(0.4), ty + Inches(0.08), SLIDE_W - Inches(0.8), Inches(0.5),
         fill_color=RGBColor(0x1A, 0x52, 0x76))
add_text(s, "☞  무료체험 예약 / 네이버 톡톡 기능 추가로 예비 관원 학부모 소통 편의성 제고 → 전방위 마케팅 활용 가능",
         Inches(0.6), ty + Inches(0.12), SLIDE_W - Inches(1.2), Inches(0.38),
         font_size=11.5, bold=True, color=C_GOLD)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 8 – AI 젬스 자동화 시스템
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_NAVY)
add_rect(s, 0, 0, Inches(0.18), SLIDE_H, fill_color=C_GOLD)
footer_band(s); slide_number(s, 8)

add_text(s, "AI 젬스(Gems) 자동화 시스템  구축", Inches(0.4), Inches(0.2),
         Inches(12), Inches(0.65), font_size=28, bold=True, color=C_WHITE)
add_text(s, "제미나이 젬스(Gemini Gems) 3종 + AI 홍보이미지 → 완전 자립형 마케팅 시스템",
         Inches(0.4), Inches(0.82), Inches(12), Inches(0.38),
         font_size=13, color=RGBColor(0xBB, 0xCC, 0xEE))

gems = [
    ("GEMS 1", "인스타 포스팅 생성기",
     "📸  사진만 넣으면\n인스타 텍스트 + 해시태그 자동 생성",
     "주 2회 포스팅\n5분 이내 완성", C_GOLD),
    ("GEMS 2", "리뷰 요청 카톡 생성기",
     "💬  학부모에게 부담 없는\n개인 맞춤 리뷰 요청 메시지 자동 작성",
     "3개월 리뷰 30개\n달성 핵심 도구", C_GREEN),
    ("GEMS 3", "리뷰 답글 생성기",
     "⭐  네이버 플레이스 리뷰 입력 시\n전문적인 감사 답글 자동 생성",
     "신뢰도 제고\n응답률 100%", C_MID),
    ("AI 이미지", "홍보 이미지 생성",
     "🎨  챗GPT · 제미나이 활용\n아이 초상권 보호 일러스트 제작",
     "홍보물 외주비\n제로", C_ORANGE),
]

gw = (SLIDE_W - Inches(0.8) - Inches(0.3) * 3) / 4
gx = Inches(0.4)
gy = Inches(1.45)
gh = Inches(5.55)

for badge, title, desc, result, color in gems:
    add_rect(s, gx, gy, gw, gh,
             fill_color=RGBColor(0x10, 0x22, 0x4A),
             line_color=color, line_width=Pt(2))
    add_rect(s, gx, gy, gw, Inches(0.6), fill_color=color)
    add_text(s, badge, gx + Inches(0.1), gy + Inches(0.08),
             gw - Inches(0.15), Inches(0.46), font_size=18, bold=True,
             color=C_WHITE)
    add_text(s, title, gx + Inches(0.1), gy + Inches(0.75),
             gw - Inches(0.15), Inches(0.55), font_size=13.5, bold=True,
             color=color)
    # desc
    dy = gy + Inches(1.4)
    for line in desc.split("\n"):
        add_text(s, line, gx + Inches(0.1), dy, gw - Inches(0.2), Inches(0.48),
                 font_size=11, color=RGBColor(0xCC, 0xDD, 0xFF))
        dy += Inches(0.44)

    # result badge
    add_rect(s, gx + Inches(0.1), gy + gh - Inches(1.0),
             gw - Inches(0.2), Inches(0.85), fill_color=color)
    for j, line in enumerate(result.split("\n")):
        add_text(s, line, gx + Inches(0.12), gy + gh - Inches(0.98) + j * Inches(0.4),
                 gw - Inches(0.24), Inches(0.38), font_size=11, bold=True,
                 color=C_WHITE, align=PP_ALIGN.CENTER)

    gx += gw + Inches(0.3)

# Workflow banner
add_rect(s, Inches(0.4), SLIDE_H - Inches(0.5), SLIDE_W - Inches(0.8), Inches(0.28),
         fill_color=RGBColor(0x0A, 0x15, 0x30))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 9 – 관원 구성 분석 & 타깃 전략
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "04-2  관원 구성 데이터 분석", "출석부 기반 연령별 분석 → 마케팅 타깃 전략 반영")
footer_band(s); slide_number(s, 9)

# Table
member_rows = [
    ("7세",         "10명", "15.4%", "초등 입학 준비 전문성 어필",        C_GOLD),
    ("1학년",        "8명",  "12.3%", "유치부 → 초등 자연스러운 연계",     C_MID),
    ("2학년",        "4명",  "6.2%",  "기초 체력 형성기 집중 케어",         C_MID),
    ("3학년",       "11명", "16.9%", "기초 체력 단단한 허리층 타깃",       C_GREEN),
    ("4학년",        "9명", "13.8%", "학교 체육 및 교우관계 연계 부각",    C_GREEN),
    ("고학년+중등", "26명", "40.0%", "독보적 경쟁력: 장기 유지 신뢰감",  C_RED),
    ("합 계",       "65명", "100%",  "역삼동 중심가 안정적 운영 증명",     C_NAVY),
]

thead = ["연령대", "인원", "비율", "마케팅 포인트"]
tcols_x  = [Inches(0.4), Inches(2.0), Inches(3.05), Inches(3.95)]
tcols_w  = [Inches(1.55), Inches(1.0),  Inches(0.85), Inches(5.2)]

ty = Inches(1.6)
for j, (label, cw) in enumerate(zip(thead, tcols_w)):
    add_rect(s, tcols_x[j], ty, cw, Inches(0.42), fill_color=C_NAVY)
    add_text(s, label, tcols_x[j] + Inches(0.05), ty + Inches(0.05),
             cw - Inches(0.08), Inches(0.34), font_size=12, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)

ty += Inches(0.42)
for i, (age, cnt, pct, tip, color) in enumerate(member_rows):
    rh = Inches(0.56)
    bg = C_WHITE if i % 2 == 0 else RGBColor(0xF0, 0xF4, 0xFA)
    is_last = (i == len(member_rows) - 1)
    for j, (txt, cw) in enumerate(zip([age, cnt, pct, tip], tcols_w)):
        fc = color if j == 0 else C_DARK_TEXT
        fw = True if j == 0 else False
        bgc = color if is_last else bg
        fgc = C_WHITE if is_last else fc
        add_rect(s, tcols_x[j], ty, cw, rh,
                 fill_color=bgc,
                 line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(0.5))
        add_text(s, txt, tcols_x[j] + Inches(0.06), ty + Inches(0.08),
                 cw - Inches(0.1), rh - Inches(0.12),
                 font_size=10.5, bold=fw, color=fgc, align=PP_ALIGN.CENTER if j < 3 else PP_ALIGN.LEFT)
    ty += rh

# Visual bar chart (right side)
rx = Inches(9.35)
ry = Inches(1.6)
rw = Inches(3.55)

add_rect(s, rx, ry, rw, Inches(0.42), fill_color=C_MID)
add_text(s, "연령별 비율 시각화", rx + Inches(0.1), ry + Inches(0.06),
         rw - Inches(0.15), Inches(0.35), font_size=12, bold=True, color=C_WHITE)

bar_data = [
    ("7세",          15.4, C_GOLD),
    ("1학년",         12.3, C_MID),
    ("2학년",          6.2, C_MID),
    ("3학년",         16.9, C_GREEN),
    ("4학년",         13.8, C_GREEN),
    ("고학년+중등",  40.0, C_RED),
]
by = ry + Inches(0.52)
max_bar = rw - Inches(1.2)
for label, pct, color in bar_data:
    bh = Inches(0.38)
    bw = max_bar * pct / 40.0  # scale to max 40%
    add_rect(s, rx + Inches(0.05), by, rw - Inches(0.1), bh,
             fill_color=RGBColor(0xE8, 0xED, 0xF5))
    add_rect(s, rx + Inches(0.05), by, bw + Inches(0.05), bh, fill_color=color)
    add_text(s, f"{label}  {pct}%", rx + Inches(0.1), by + Inches(0.04),
             rw - Inches(0.15), bh - Inches(0.06), font_size=9.5,
             bold=True, color=C_WHITE if pct > 10 else C_DARK_TEXT)
    by += bh + Inches(0.1)

# Key insight
add_rect(s, Inches(0.4), by + Inches(0.15), SLIDE_W - Inches(0.8), Inches(0.95),
         fill_color=C_NAVY)
add_text(s, "☞  고학년+중등 비율 40% — 일반적으로 학과 공부로 이탈하는 연령대가 전체의 40%를 차지\n"
            "→  \"한 번 믿고 보내면 끝까지 안심하고 맡기는 도장\" 의 가장 강력한 객관적 마케팅 근거",
         Inches(0.6), by + Inches(0.18), SLIDE_W - Inches(1.2), Inches(0.75),
         font_size=11.5, bold=True, color=C_GOLD)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 10 – 3회차 컨설팅 & 자립 완성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "05  3회차 컨설팅", "2026.05.29 | 자립 실습 완료 · 리뷰 성장 계획 · 시스템 총정리")
footer_band(s); slide_number(s, 10)

# Left – 자립 실습
lw = Inches(6.1)
add_rect(s, Inches(0.4), Inches(1.6), lw, Inches(5.55),
         fill_color=C_WHITE, line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(1))
add_rect(s, Inches(0.4), Inches(1.6), lw, Inches(0.5), fill_color=C_GREEN)
add_text(s, "자립 실습 완료 내용", Inches(0.6), Inches(1.65),
         lw - Inches(0.2), Inches(0.42), font_size=14, bold=True, color=C_WHITE)

practice_items = [
    ("✅", "젬스 3번 리뷰 답글 생성기 활용",
     "네이버 플레이스 기존 리뷰 답글 실제 등록 완료"),
    ("✅", "젬스 1번 인스타 포스팅 생성기 활용",
     "인스타그램 2번째 포스팅 업로드 확인 (품질 조정 완료)"),
    ("✅", "10분 이내 완성 루틴 완전 체득",
     "사진 촬영(1분) → 젬스 문구 생성(2분) → 업로드(2분) = 총 5분"),
    ("✅", "네이버 플레이스 보완 완료",
     "무료체험 예약 + 네이버 톡톡 기능 추가"),
    ("✅", "AI 홍보 이미지 생성 실습",
     "챗GPT·제미나이 활용 초상권 보호 일러스트 제작"),
]
py3 = Inches(2.25)
for icon, title, desc in practice_items:
    add_text(s, icon, Inches(0.55), py3, Inches(0.35), Inches(0.45),
             font_size=14, color=C_GREEN)
    add_text(s, title, Inches(0.9), py3, lw - Inches(0.6), Inches(0.3),
             font_size=11.5, bold=True, color=C_DARK_TEXT)
    add_text(s, desc, Inches(0.9), py3 + Inches(0.28), lw - Inches(0.6), Inches(0.28),
             font_size=10, color=C_GREY)
    add_rect(s, Inches(0.55), py3 + Inches(0.55), lw - Inches(0.3), Inches(0.008),
             fill_color=RGBColor(0xE0, 0xE8, 0xF5))
    py3 += Inches(0.62)

# Right – 리뷰 성장 계획
rx = Inches(6.85)
rw = Inches(6.1)
add_rect(s, rx, Inches(1.6), rw, Inches(0.5), fill_color=C_RED)
add_text(s, "리뷰 30개 달성 실행 계획 (3개월)", rx + Inches(0.15), Inches(1.65),
         rw - Inches(0.2), Inches(0.42), font_size=14, bold=True, color=C_WHITE)

timings = [
    ("신규 등록 1개월 후", "적응 완료 → 만족도 최고점"),
    ("승급 심사 직후",     "성취감 최고조 → 긍정 리뷰 자연 유도"),
    ("야간수련·이벤트 직후","특별 경험 → 감동 공유 욕구"),
    ("부모 감사 표현 시",  "자발적 만족 상태 → 최적 타이밍"),
]
ty2 = Inches(2.25)
add_text(s, "최적 리뷰 요청 타이밍", rx + Inches(0.1), ty2,
         rw - Inches(0.2), Inches(0.3), font_size=11.5, bold=True, color=C_MID)
ty2 += Inches(0.35)

for timing, reason in timings:
    add_rect(s, rx + Inches(0.1), ty2, rw - Inches(0.2), Inches(0.54),
             fill_color=RGBColor(0xF0, 0xF4, 0xFA),
             line_color=C_RED, line_width=Pt(0.75))
    add_rect(s, rx + Inches(0.1), ty2, Inches(0.12), Inches(0.54), fill_color=C_RED)
    add_text(s, timing, rx + Inches(0.28), ty2 + Inches(0.04),
             rw - Inches(0.45), Inches(0.26), font_size=10.5, bold=True, color=C_DARK_TEXT)
    add_text(s, reason, rx + Inches(0.28), ty2 + Inches(0.28),
             rw - Inches(0.45), Inches(0.24), font_size=9.5, color=C_GREY)
    ty2 += Inches(0.62)

# Target progress bar
ty2 += Inches(0.1)
add_rect(s, rx, ty2, rw, Inches(0.42), fill_color=C_MID)
add_text(s, "리뷰 목표: 현재 13개 → 3개월 내 30개 이상", rx + Inches(0.1), ty2 + Inches(0.06),
         rw - Inches(0.2), Inches(0.35), font_size=11.5, bold=True, color=C_WHITE)
ty2 += Inches(0.52)
bar_bg_w = rw - Inches(0.4)
add_rect(s, rx + Inches(0.2), ty2, bar_bg_w, Inches(0.45),
         fill_color=RGBColor(0xD8, 0xE4, 0xF0))
add_rect(s, rx + Inches(0.2), ty2, bar_bg_w * 13 / 30, Inches(0.45),
         fill_color=C_ORANGE)
add_text(s, "현재 13개", rx + Inches(0.25), ty2 + Inches(0.1),
         Inches(1.5), Inches(0.3), font_size=9.5, bold=True, color=C_WHITE)
add_rect(s, rx + Inches(0.2) + bar_bg_w * 13 / 30, ty2,
         bar_bg_w * 17 / 30, Inches(0.45),
         fill_color=RGBColor(0xB0, 0xC8, 0xE0))
add_text(s, "목표 +17개", rx + Inches(0.2) + bar_bg_w * 13 / 30 + Inches(0.1),
         ty2 + Inches(0.1), Inches(1.5), Inches(0.3),
         font_size=9.5, bold=True, color=C_DARK_TEXT)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 11 – 컨설팅 성과 Before/After
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "06  컨설팅 성과 비교", "Before → After  전후 비교")
footer_band(s); slide_number(s, 11)

ba_items = [
    ("네이버 플레이스 운영",
     "운영 미흡\n(리뷰 댓글 無 / 소식 無 / 정보 불일치)",
     "전면 정비 완료\n메뉴구성 · 콘텐츠 · 댓글 · 소식 업데이트"),
    ("마케팅 문구 작성",
     "인스타/블로그 문구\n자체 작성 불가",
     "AI 젬스 3종 + 매뉴얼 제공\n→  클릭 한 번으로 자동 생성"),
    ("홍보물 제작",
     "홍보물 자체 제작\n완전 불가",
     "챗GPT · 제미나이 활용\n초상권 보호 일러스트 자유 제작"),
    ("운영 루틴",
     "마케팅 루틴\n전무",
     "주 2회 10분 루틴 확립\n(촬영 1분 + 젬스 2분 + 업로드 2분)"),
]

col_before_x = Inches(2.0)
col_after_x  = Inches(7.1)
cw_ba        = Inches(4.8)
ty_ba        = Inches(1.62)

add_rect(s, Inches(0.4),  ty_ba, Inches(1.55), Inches(0.44), fill_color=C_GREY)
add_text(s, "항 목", Inches(0.45), ty_ba + Inches(0.06),
         Inches(1.5), Inches(0.35), font_size=12, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_rect(s, col_before_x, ty_ba, cw_ba, Inches(0.44), fill_color=C_RED)
add_text(s, "BEFORE  컨설팅 이전", col_before_x + Inches(0.1), ty_ba + Inches(0.06),
         cw_ba - Inches(0.2), Inches(0.35), font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_rect(s, col_after_x, ty_ba, cw_ba, Inches(0.44), fill_color=C_GREEN)
add_text(s, "AFTER  컨설팅 이후", col_after_x + Inches(0.1), ty_ba + Inches(0.06),
         cw_ba - Inches(0.2), Inches(0.35), font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

ty_ba += Inches(0.44)
for i, (label, before, after) in enumerate(ba_items):
    rh = Inches(0.98)
    bg = C_WHITE if i % 2 == 0 else RGBColor(0xF0, 0xF5, 0xFF)
    add_rect(s, Inches(0.4), ty_ba, Inches(1.55), rh,
             fill_color=RGBColor(0xE8, 0xED, 0xF5),
             line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(0.5))
    add_text(s, label, Inches(0.45), ty_ba + Inches(0.08),
             Inches(1.48), rh - Inches(0.12), font_size=10, bold=True,
             color=C_NAVY, align=PP_ALIGN.CENTER)
    add_rect(s, col_before_x, ty_ba, cw_ba, rh,
             fill_color=RGBColor(0xFF, 0xF0, 0xF0),
             line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(0.5))
    add_text(s, before, col_before_x + Inches(0.12), ty_ba + Inches(0.12),
             cw_ba - Inches(0.2), rh - Inches(0.18), font_size=10.5, color=C_DARK_TEXT)
    # arrow
    add_text(s, "➜", Inches(6.8), ty_ba + Inches(0.3), Inches(0.5), Inches(0.44),
             font_size=22, bold=True, color=C_MID, align=PP_ALIGN.CENTER)
    add_rect(s, col_after_x, ty_ba, cw_ba, rh,
             fill_color=RGBColor(0xF0, 0xFF, 0xF4),
             line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(0.5))
    add_text(s, after, col_after_x + Inches(0.12), ty_ba + Inches(0.12),
             cw_ba - Inches(0.2), rh - Inches(0.18), font_size=10.5,
             color=C_GREEN, bold=True)
    ty_ba += rh + Inches(0.06)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 12 – 자립형 마케팅 루틴
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_NAVY)
add_rect(s, 0, 0, Inches(0.18), SLIDE_H, fill_color=C_GREEN)
footer_band(s); slide_number(s, 12)

add_text(s, "자립형 마케팅 루틴", Inches(0.4), Inches(0.2),
         Inches(10), Inches(0.65), font_size=32, bold=True, color=C_WHITE)
add_text(s, "주 2회  10분 마케팅 루틴으로 컨설팅 이후에도 지속 가능한 성장",
         Inches(0.4), Inches(0.82), Inches(12), Inches(0.38),
         font_size=14, color=RGBColor(0xBB, 0xCC, 0xEE))

# Weekly routine visual
routine_steps = [
    ("1분", "사진 촬영", "수련 뒷모습\n시설 모습", C_GOLD),
    ("2분", "젬스 문구 생성", "인스타 텍스트\n+ 해시태그 자동", C_MID),
    ("2분", "업로드 완료", "인스타그램\n포스팅 완성", C_GREEN),
    ("별도", "리뷰 요청", "젬스 2번 활용\n개별 맞춤 카톡", C_ORANGE),
    ("즉시", "리뷰 답글", "젬스 3번 활용\n감사 답글 자동", C_RED),
]

sw = (SLIDE_W - Inches(0.8) - Inches(0.25) * 4) / 5
sx = Inches(0.4)
sy = Inches(1.5)

for i, (time, title, desc, color) in enumerate(routine_steps):
    sh = Inches(2.8)
    add_rect(s, sx, sy, sw, sh,
             fill_color=RGBColor(0x10, 0x22, 0x4A),
             line_color=color, line_width=Pt(2))
    add_rect(s, sx, sy, sw, Inches(0.5), fill_color=color)
    add_text(s, time, sx + Inches(0.05), sy + Inches(0.06),
             sw - Inches(0.1), Inches(0.4), font_size=20, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text(s, title, sx + Inches(0.08), sy + Inches(0.62),
             sw - Inches(0.12), Inches(0.55), font_size=13, bold=True,
             color=color, align=PP_ALIGN.CENTER)
    for j, line in enumerate(desc.split("\n")):
        add_text(s, line, sx + Inches(0.08), sy + Inches(1.28) + j * Inches(0.38),
                 sw - Inches(0.12), Inches(0.36), font_size=10.5,
                 color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.CENTER)
    # connector arrow
    if i < 4:
        add_rect(s, sx + sw, sy + Inches(1.1),
                 Inches(0.25), Inches(0.3), fill_color=color)
    sx += sw + Inches(0.25)

# Total time badge
add_rect(s, Inches(0.4), Inches(4.45), SLIDE_W - Inches(0.8), Inches(0.65),
         fill_color=C_GREEN)
add_text(s, "⏱  총 5분 이내 완성 — 스마트폰 하나로 전문적인 마케팅 콘텐츠 제작 가능",
         Inches(0.6), Inches(4.55), SLIDE_W - Inches(1.2), Inches(0.52),
         font_size=16, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

# Monthly checklist
checklists = [
    ("네이버 플레이스",    "✅ 정보 최신화\n✅ 리뷰 답글 등록\n✅ 소식 게시"),
    ("인스타그램",         "✅ 주 2회 포스팅\n✅ 해시태그 최적화\n✅ 팔로워 소통"),
    ("리뷰 관리",          "✅ 개별 요청 발송\n✅ 답글 즉시 등록\n✅ 리뷰 30개 목표"),
    ("환경개선",           "✅ 계단/복도 청결\n✅ 비포·애프터 기록\n✅ 학부모 첫인상 관리"),
]
cx = Inches(0.4)
cw_check = (SLIDE_W - Inches(0.8) - Inches(0.3) * 3) / 4
for title, items in checklists:
    add_rect(s, cx, Inches(5.2), cw_check, Inches(0.38), fill_color=C_MID)
    add_text(s, title, cx + Inches(0.08), Inches(5.23), cw_check - Inches(0.1),
             Inches(0.3), font_size=11, bold=True, color=C_WHITE)
    add_rect(s, cx, Inches(5.58), cw_check, Inches(1.5),
             fill_color=RGBColor(0x10, 0x22, 0x4A),
             line_color=C_MID, line_width=Pt(1))
    ity = Inches(5.65)
    for line in items.split("\n"):
        add_text(s, line, cx + Inches(0.1), ity, cw_check - Inches(0.15), Inches(0.38),
                 font_size=9.5, color=RGBColor(0xCC, 0xDD, 0xFF))
        ity += Inches(0.36)
    cx += cw_check + Inches(0.3)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 13 – 자립 시스템 총정리 체크리스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "05-2  자립 시스템 총정리", "컨설팅 종료 시점 구축 완료 현황")
footer_band(s); slide_number(s, 13)

systems = [
    (C_GREEN,  "✅", "네이버 플레이스 최적화 및 업데이트",
     "브랜드 통일 · 운영시간 · 소개글 · 사진 · 핵심 서비스 전면 정비 완료\n무료체험 예약 + 네이버 톡톡 추가 → 예비 관원 소통 채널 확보"),
    (C_GREEN,  "✅", "인스타그램 공식 채널 정상 가동",
     "역삼효태권도장 공식 인스타그램 개설 · 첫 포스팅 업로드 완료\n관장님 직접 실습으로 지속 운영 역량 확보"),
    (C_GREEN,  "✅", "AI 젬스 4종 완전 체득 및 실습 완료",
     "인스타 포스팅 생성기 / 리뷰 요청 카톡 생성기 / 리뷰 답글 생성기\nAI 홍보이미지 생성 → 젬스 활용 매뉴얼 제작 및 숙지 확인"),
    (C_GREEN,  "✅", "주 2회 10분 마케팅 루틴 확립",
     "사진 촬영(1분) + 젬스 활용(2분) + 업로드(2분) = 5분 이내 완성 루틴\n외부 대행 없이 스스로 지속 가능한 자립형 마케팅 시스템"),
    (C_GREEN,  "✅", "리뷰 30개 달성 단계별 실행 계획 수립",
     "현재 13개 → 3개월 내 30개 목표 · 최적 타이밍별 요청 전략 확정\n젬스 2번 활용 개별 맞춤 발송으로 강요 없는 자연스러운 리뷰 확보"),
    (C_GOLD,   "✅", "환경개선 및 학부모 눈높이 소통 의지",
     "계단·복도 청결 환경개선 (첫인상 관리)\n비포·애프터 이미지화 및 서울시 소상공인 지원사업 연계 안내"),
]

sy_c = Inches(1.62)
for color, icon, title, desc in systems:
    rh = Inches(0.78)
    add_rect(s, Inches(0.4), sy_c, SLIDE_W - Inches(0.8), rh,
             fill_color=C_WHITE, line_color=RGBColor(0xCC, 0xD8, 0xEC), line_width=Pt(0.75))
    add_rect(s, Inches(0.4), sy_c, Inches(0.55), rh, fill_color=color)
    add_text(s, icon, Inches(0.41), sy_c + Inches(0.18),
             Inches(0.52), Inches(0.42), font_size=20, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text(s, title, Inches(1.05), sy_c + Inches(0.06),
             Inches(4.8), Inches(0.34), font_size=13, bold=True, color=C_DARK_TEXT)
    add_text(s, desc, Inches(1.05), sy_c + Inches(0.38),
             SLIDE_W - Inches(1.55), Inches(0.38), font_size=10, color=C_GREY)
    sy_c += rh + Inches(0.07)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 14 – 향후 제언
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_LIGHT)
header_band(s, "07  향후 제언", "지속 가능성 및 성장 전략 제언")
footer_band(s); slide_number(s, 14)

recs = [
    (C_RED, "단톡방 유지를 통한 사후 관리",
     "컨설팅 팀과 단체 채팅방 유지로 추후 궁금증 즉시 해결\n지속적인 관리 및 피드백 제공 예정"),
    (C_GOLD, "WOM(입소문) 마케팅 활용",
     "컨설팅 수혜 업체가 주변 소상공인 대상으로 홍보\n→ 추천제도 운영으로 선순환 생태계 구축 제언"),
    (C_GREEN, "서울시 소상공인 지원사업 연계",
     "서울특별시 소상공인 지원사업 (seoulsbdc.or.kr) 활용\n하반기 시설개선 지원 300만원 → 계단·복도 환경개선 비용 절감"),
    (C_MID, "콘텐츠 자산 지속 축적",
     "수련 사진·영상 꾸준한 기록 → 인스타그램·네이버 플레이스 콘텐츠 자산화\n\"가랑비에 옷 젖듯이\" 철학을 온라인에서도 실현"),
]

rw2 = (SLIDE_W - Inches(0.8) - Inches(0.3)) / 2
ry2 = Inches(1.62)
for i, (color, title, desc) in enumerate(recs):
    rx2 = Inches(0.4) if i % 2 == 0 else Inches(0.4) + rw2 + Inches(0.3)
    ry2_current = Inches(1.62) if i < 2 else Inches(4.1)
    rh2 = Inches(2.3)
    add_rect(s, rx2, ry2_current, rw2, rh2,
             fill_color=C_WHITE, line_color=color, line_width=Pt(1.5))
    add_rect(s, rx2, ry2_current, rw2, Inches(0.5), fill_color=color)
    add_text(s, f"0{i+1}  {title}", rx2 + Inches(0.12), ry2_current + Inches(0.07),
             rw2 - Inches(0.2), Inches(0.4), font_size=13, bold=True, color=C_WHITE)
    dy2 = ry2_current + Inches(0.62)
    for line in desc.split("\n"):
        add_text(s, f"• {line}", rx2 + Inches(0.15), dy2,
                 rw2 - Inches(0.25), Inches(0.42), font_size=11, color=C_DARK_TEXT)
        dy2 += Inches(0.44)

# Quote box
add_rect(s, Inches(0.4), SLIDE_H - Inches(1.0), SLIDE_W - Inches(0.8), Inches(0.65),
         fill_color=C_NAVY)
add_text(s, "\"태권도 학원들이 대체로 홍보 마케팅과 거리가 멀었는데, 3일 동안 완전히! "
            "꼭 필요한 것을 너무나도 꽉꽉 채워주셨습니다. 감사합니다!\"",
         Inches(0.6), SLIDE_H - Inches(0.95), SLIDE_W - Inches(1.2), Inches(0.58),
         font_size=12, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SLIDE 15 – CLOSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
s = new_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill_color=C_NAVY)
add_rect(s, 0, 0, Inches(0.55), SLIDE_H, fill_color=C_RED)
# bottom gold stripe
add_rect(s, 0, SLIDE_H - Inches(0.25), SLIDE_W, Inches(0.25), fill_color=C_GOLD)

# Background circles
for cx2, cy2, cr, col in [
    (SLIDE_W - Inches(2.5), Inches(-1.0), Inches(4.5), RGBColor(0x14, 0x28, 0x55)),
    (SLIDE_W - Inches(1.0), SLIDE_H - Inches(1.5), Inches(3.0), RGBColor(0x0A, 0x15, 0x30)),
]:
    c = s.shapes.add_shape(9, cx2, cy2, cr, cr)
    c.fill.solid(); c.fill.fore_color.rgb = col
    c.line.fill.background()

add_text(s, "감사합니다", Inches(0.9), Inches(1.5),
         Inches(9), Inches(1.2), font_size=58, bold=True, color=C_WHITE)
add_rect(s, Inches(0.9), Inches(2.75), Inches(4.5), Inches(0.06), fill_color=C_GOLD)

add_text(s, "역삼효태권도장  온라인 마케팅 컨설팅 보고서",
         Inches(0.9), Inches(2.95), Inches(11), Inches(0.55),
         font_size=18, color=RGBColor(0xBB, 0xCC, 0xEE))

summary_points = [
    "✅  네이버 플레이스 완전 최적화 및 브랜드 통일",
    "✅  인스타그램 공식 채널 개설 및 첫 포스팅 완료",
    "✅  AI 젬스 3종 자동화 시스템 완전 체득",
    "✅  주 2회 10분 마케팅 루틴 자립 시스템 완성",
    "✅  3개월 리뷰 30개 달성 단계별 실행 계획 수립",
]
sy2 = Inches(3.65)
for pt in summary_points:
    add_text(s, pt, Inches(0.9), sy2, Inches(8), Inches(0.42),
             font_size=13.5, color=C_WHITE)
    sy2 += Inches(0.5)

# Team info
add_rect(s, Inches(0.9), SLIDE_H - Inches(1.1), Inches(7), Inches(0.65),
         fill_color=RGBColor(0x14, 0x28, 0x55))
add_text(s, "컨설팅 팀: B그룹 5조  |  권용준, 손미현  |  2026.05.26 ~ 2026.05.29",
         Inches(1.0), SLIDE_H - Inches(1.05), Inches(6.8), Inches(0.55),
         font_size=12, color=RGBColor(0xBB, 0xCC, 0xEE))

slide_number(s, 15)

# ─── Save ──────────────────────────────────────────────────────────────────────
out_path = "/home/user/-/역삼효태권도장_온라인마케팅컨설팅_보고서.pptx"
prs.save(out_path)
print(f"Saved: {out_path}")
