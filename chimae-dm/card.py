# -*- coding: utf-8 -*-
"""
정보성 카드뉴스 생성기 (Pillow)

치매간병보험 DM과 함께 보낼 정보 카드(PNG)를 코드로 정확히 찍어낸다.
AI 이미지 생성기와 달리 한글·숫자·법적 문구가 깨지지 않는다.

카드 1장 = DM 1통의 시각 버전. 하단에 '훅' 질문을 넣어 답장을 유도한다.
"""
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
FONT_DIR = BASE / "fonts"
F_BOLD = str(FONT_DIR / "NotoSansKR-Bold.otf")
F_REG  = str(FONT_DIR / "NotoSansKR-Regular.otf")

# ── 색상 팔레트 ──
NAVY   = "#1f3a5f"
CORAL  = "#e8533f"
GRAY   = "#5f6c7b"
LIGHT  = "#f4f7fb"
WHITE  = "#ffffff"
HOOKBG = "#fff4e6"
HOOKTX = "#b35309"

W, H = 1080, 1350   # 모바일 세로형


def _font(path, size):
    return ImageFont.truetype(path, size)


def _wrap(draw, text, font, max_w):
    """글자 단위로 너비에 맞춰 줄바꿈 (한글은 단어 경계가 약해 문자 기준)."""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        test = cur + ch
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def _draw_multiline(draw, xy, text, font, fill, max_w, line_gap=14):
    x, y = xy
    for line in _wrap(draw, text, font, max_w):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def make_card(
    out_path: str,
    badge: str,
    headline: str,
    big: str = "",
    body: str = "",
    hook: str = "",
    footer: str = "본 자료는 정보 제공 목적이며, 자세한 사항은 약관을 확인하세요.",
    is_ad: bool = False,
):
    """정보 카드 PNG 1장 생성."""
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    pad = 80
    maxw = W - pad * 2

    # 상단 컬러 바
    d.rectangle([0, 0, W, 18], fill=NAVY)

    y = 90
    # 광고 표기 (법규)
    if is_ad:
        d.rounded_rectangle([pad, y, pad + 150, y + 50], radius=10, fill=CORAL)
        d.text((pad + 28, y + 8), "광고", font=_font(F_BOLD, 30), fill=WHITE)
        y += 78

    # 배지
    bf = _font(F_BOLD, 34)
    bw = d.textlength(badge, font=bf)
    d.rounded_rectangle([pad, y, pad + bw + 44, y + 60], radius=14, fill=LIGHT)
    d.text((pad + 22, y + 10), badge, font=bf, fill=NAVY)
    y += 100

    # 헤드라인 (강조)
    y = _draw_multiline(d, (pad, y), headline, _font(F_BOLD, 58), NAVY, maxw, 18)
    y += 24

    # 큰 숫자/강조 문구
    if big:
        bigf = _font(F_BOLD, 92)
        for line in _wrap(d, big, bigf, maxw):
            d.text((pad, y), line, font=bigf, fill=CORAL)
            y += bigf.size + 10
        y += 24

    # 본문
    if body:
        y = _draw_multiline(d, (pad, y), body, _font(F_REG, 40), GRAY, maxw, 16)
        y += 20

    # 훅 박스 (하단 고정 영역 위)
    if hook:
        hook_lines = _wrap(d, hook, _font(F_BOLD, 40), maxw - 60)
        box_h = 56 + len(hook_lines) * (40 + 12)
        box_top = H - 220 - box_h
        d.rounded_rectangle([pad, box_top, W - pad, box_top + box_h],
                            radius=20, fill=HOOKBG)
        # 말풍선 아이콘 (이모지 대신 직접 그림 — 폰트 깨짐 방지)
        ix, iy = pad + 30, box_top + 24
        d.rounded_rectangle([ix, iy, ix + 42, iy + 30], radius=8, fill=HOOKTX)
        d.polygon([(ix + 10, iy + 30), (ix + 22, iy + 30), (ix + 10, iy + 42)],
                  fill=HOOKTX)
        d.text((ix + 56, box_top + 22), "이렇게 답장 주세요",
               font=_font(F_BOLD, 30), fill=HOOKTX)
        yy = box_top + 70
        for line in hook_lines:
            d.text((pad + 30, yy), line, font=_font(F_BOLD, 40), fill=HOOKTX)
            yy += 40 + 12

    # 하단 푸터
    d.line([pad, H - 150, W - pad, H - 150], fill="#dfe5ec", width=2)
    _draw_multiline(d, (pad, H - 130), footer, _font(F_REG, 24), GRAY, maxw, 8)

    img.save(out_path)
    return out_path


# ── 7일 시퀀스 카드 콘텐츠 (knowledge 기반, 텍스트는 카드용으로 압축) ──
def card_specs():
    """일자별 카드 사양. (text DM과 짝이 되는 시각 버전)"""
    return [
        dict(day=1, badge="안부", headline="환절기,\n건강 잘 챙기세요",
             big="", body="늘 마음 쓰며 안부 전합니다.\n오늘도 평안한 하루 되세요.",
             hook="두 분 부모님 모두 건강하시죠?", is_ad=False),
        dict(day=2, badge="치매 현실", headline="이제 10명 중 1명",
             big="105만 명", body="2025년 65세 이상 추정 치매환자 수.\n더는 남의 일이 아닙니다.",
             hook="주변에 치매로 고생하신 분, 보신 적 있으세요?", is_ad=False),
        dict(day=3, badge="간병 비용", headline="간병은 가족 모두의 부담",
             big="연 2,639만 원", body="치매환자 1인당 연간 관리비용.\n장기요양보험을 써도 본인부담 20%는 남습니다.",
             hook="부모님 연세가 어떻게 되세요? 해당되는 걸 정리해 드릴게요.", is_ad=False),
        dict(day=4, badge="치료비", headline="신약 시대의 명암",
             big="6,480만 원", body="표적치매약물 '레켐비' 18개월 투약 비용.\n진행을 27% 늦추지만 대부분 비급여입니다.",
             hook="내일은 '지금 보험으로 충분한지' 확인하는 법을 알려드릴게요.", is_ad=False),
        dict(day=5, badge="보험 점검", headline="정작 필요할 때\n비어 있지 않나요?",
             big="", body="갱신형은 납입면제돼도 갱신 후 다시 납입이 재개됩니다.\n환급금 노려 65세에 해지하면 가장 위험한 시기에 보장이 사라져요.",
             hook="지금 치매보험이 갱신형인지 아세요? 증권번호만 주시면 확인해 드려요.", is_ad=True),
        dict(day=6, badge="해결책", headline="해지하지 않아도 충분하게",
             big="", body="비갱신형 + 전기간(100세) 납입면제.\n검사·진단·치료·입원·통원까지 단계별 보장.",
             hook="보험료·보장범위·납입면제 중 뭐가 제일 궁금하세요?", is_ad=True),
        dict(day=7, badge="무료 점검", headline="강요는 없습니다",
             big="", body="지금 보험으로 충분한지 '점검'만 무료로 도와드립니다.\n필요하실 때 편히 말씀 주세요.",
             hook="점검 받아보실래요? 네/아니요만 주셔도 됩니다.", is_ad=True),
    ]


def build_all(out_dir: str, agent: str = ""):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    foot_base = "정보 제공 목적 · 자세한 사항은 약관 확인"
    for s in card_specs():
        foot = foot_base + (f" · {agent}" if agent else "")
        if s["is_ad"]:
            foot = "(광고) " + foot_base + " · 무료수신거부 080-XXX-XXXX"
        p = os.path.join(out_dir, f"card_day{s['day']}.png")
        make_card(p, badge=s["badge"], headline=s["headline"], big=s["big"],
                  body=s["body"], hook=s["hook"], footer=foot, is_ad=s["is_ad"])
        paths.append(p)
    return paths


if __name__ == "__main__":
    out = build_all(str(BASE / "out"), agent="박철수 설계사")
    print("생성된 카드:")
    for p in out:
        print(" ", p)
