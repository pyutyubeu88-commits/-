#!/usr/bin/env python3
"""
gpt-image-2 기반 치매간병보험 정보 카드 생성기

OpenAI 의 gpt-image-2 (ChatGPT Images 2.0, 2026.04) 로 7일 시퀀스 카드를 생성한다.
한글 렌더링 정확도가 높지만, '숫자·법정문구' 1% 오류 리스크를 없애기 위해
선택적으로 핵심 텍스트를 코드(Pillow)로 검증/오버레이할 수 있다.

실행 전제:
  export OPENAI_API_KEY=sk-...
  python gpt_image.py
"""
import base64
import os
from pathlib import Path

from openai import OpenAI

import card  # 기존 card_specs() 재사용 (그라운딩된 7일 콘텐츠)

BASE = Path(__file__).parent
OUT  = BASE / "out_gpt"

MODEL   = "gpt-image-2"
SIZE    = "1024x1536"   # 모바일 세로형 (정사각보다 저렴)
QUALITY = "high"        # low / medium / high

# ── 브랜드 / 설계사 정보 ──
# 롯데손해보험 전속설계사. 회사를 직접 대표하므로 브랜드 톤 사용이 자연스럽다.
# 단, 자체 제작 광고물(5~7일차)은 회사 광고심의를 거쳐 심의필 번호를 받아야 한다.
# 공식 로고/심볼은 회사 승인 자산(브랜드 가이드)을 받아 쓰는 것이 원칙.
AGENT_NAME = "롯데손해보험 전속설계사 권용준"
AGENT_TEL  = "010-6783-2588"   # 설계사 연락처
LOTTE_RED  = "#DA291C"   # LOTTE Red (Pantone 186C 계열, 화면용 근사값)
INK_NAVY   = "#2b2b2b"   # 본문 가독용 딥 그레이/네이비


# ── 일자별 비주얼 모티프 (디자인에 깊이와 의미 부여) ──
# 카드마다 다른 일러스트/그래픽 요소를 넣어 '템플릿 느낌'을 없앤다.
MOTIF = {
    1: "따뜻한 햇살이 드는 창가, 김이 오르는 차 한 잔, 작은 화분 — "
       "포근하고 평온한 분위기의 부드러운 플랫 일러스트를 상단/배경에 은은하게.",
    2: "대한민국 지도 또는 사람 실루엣 10개 중 1개만 코랄색으로 강조된 "
       "미니멀 인포그래픽 픽토그램. 통계의 무게감을 시각적으로.",
    3: "두 손이 어르신의 손을 감싸 쥔 따뜻한 라인 일러스트, "
       "또는 가족을 상징하는 부드러운 픽토그램. 비용의 무게를 공감으로 풀어내기.",
    4: "알약·캡슐과 의료용 작은 그래프(완만하게 꺾이는 선)를 결합한 "
       "현대적 의료 인포그래픽 요소. 신약의 명암을 절제된 톤으로.",
    5: "방패(보장) 아이콘에 살짝 금이 가거나 비어 있는 부분을 코랄로 표시한 "
       "은유적 픽토그램. '빈틈'을 직관적으로 보여주는 미니멀 그래픽.",
    6: "튼튼한 방패 또는 우산이 사람/가족을 감싸는 안정감 있는 라인 일러스트. "
       "단계별 보장을 상징하는 연결된 도트/체크 요소.",
    7: "악수 또는 편안한 상담 테이블, 따뜻한 대화 분위기의 부드러운 일러스트. "
       "강요 없는 친근함이 느껴지는 톤.",
}


def build_prompt(spec: dict) -> str:
    """카드 1장용 gpt-image-2 프롬프트. 한글 문구를 '그대로' 렌더하도록 지시."""
    ad_line = ""
    if spec["is_ad"]:
        ad_line = (
            "좌측 상단에 작고 단정한 빨간 둥근 배지로 '광고' 표기. "
            "맨 하단에 작은 회색 글씨로 '무료수신거부 080-XXX-XXXX' 표기. "
        )
    big_line = (
        f"중앙에 매우 큰 롯데 레드(#DA291C) 초굵은 숫자로 '{spec['big']}' — "
        "숫자에 살짝 입체감/그림자를 주어 시선을 사로잡되 정확히 렌더링. "
        if spec["big"] else ""
    )
    motif = MOTIF.get(spec["day"], "")

    return (
        # ── 스타일/품질 지시 (롯데손해보험 브랜드 톤) ──
        "한국 대형 보험사의 공식 카드뉴스 수준 프리미엄 디자인 1장. 모바일 세로형(1024x1536). "
        "브랜드 컨셉은 '롯데손해보험' — 깨끗한 흰색/아이보리 배경에 시그니처 컬러인 "
        "강렬한 롯데 레드(#DA291C)를 포인트로 쓰는 단정하고 신뢰감 있는 기업형 디자인. "
        "상단에 얇은 롯데 레드 라인 또는 작은 레드 액센트 바를 두어 브랜드 일관성을 준다. "
        "부드러운 그림자와 둥근 모서리 카드 레이어로 깊이감, 넉넉한 여백, 명확한 시각적 위계, "
        "세련된 산세리프 한글 타이포그래피. 본문 글자는 가독성 높은 딥 그레이(#2b2b2b). "
        "절제되고 전문적이며 따뜻한 분위기 — 자극적이거나 촌스럽지 않게.\n\n"
        # ── 비주얼 모티프 ──
        f"비주얼 요소: {motif} 일러스트는 롯데 레드와 회색 톤의 단정한 플랫/라인 스타일로, "
        "텍스트를 가리지 않게 배경/여백에 절제되어 배치.\n\n"
        # ── 텍스트 콘텐츠 (정확 렌더 필수) ──
        "아래 한국어 텍스트를 오탈자 없이 100% 정확하게 렌더링할 것 (글자 깨짐·누락 금지):\n"
        f"· 상단 둥근 배지(작게, 롯데 레드 톤): '{spec['badge']}'\n"
        f"· 큰 제목(딥 그레이/블랙, 매우 굵게, 2~3줄): '{spec['headline']}'\n"
        f"{('· ' + big_line) if big_line else ''}"
        f"· 본문(딥 그레이, 읽기 편한 크기): '{spec['body']}'\n"
        f"· 하단 둥근 연한 레드 박스 안, 말풍선 아이콘과 함께 굵은 롯데 레드 글씨: '{spec['hook']}'\n"
        f"· 맨 하단에 작고 단정한 회색 서명 한 줄: '{AGENT_NAME}  {AGENT_TEL}'\n"
        f"{ad_line}\n"
        "주의: 임의로 만든 롯데 로고/심볼/워드마크는 그리지 말 것(회사 승인 자산만 사용). "
        "브랜드 '느낌'은 롯데 레드 컬러와 단정한 기업 톤으로 표현. "
        "사람 얼굴 클로즈업이나 실사 사진은 쓰지 말고, "
        "따뜻한 플랫/라인 일러스트와 타이포그래피 중심으로 완성도 높게."
    )


def generate_card(client: OpenAI, spec: dict, out_path: Path):
    resp = client.images.generate(
        model=MODEL,
        prompt=build_prompt(spec),
        size=SIZE,
        quality=QUALITY,
    )
    img_b64 = resp.data[0].b64_json
    out_path.write_bytes(base64.b64decode(img_b64))
    return out_path


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "❌ OPENAI_API_KEY 가 없습니다.\n"
            "   export OPENAI_API_KEY=sk-...  후 다시 실행하세요."
        )
    OUT.mkdir(exist_ok=True)
    client = OpenAI()
    specs = card.card_specs()
    print(f"gpt-image-2 로 {len(specs)}장 생성 시작 (size={SIZE}, quality={QUALITY})")
    for s in specs:
        p = OUT / f"gptcard_day{s['day']}.png"
        generate_card(client, s, p)
        print(f"  ✅ {s['day']}일차 → {p}")
    print("완료. out_gpt/ 확인")


if __name__ == "__main__":
    main()
