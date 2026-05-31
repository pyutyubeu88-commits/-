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


def build_prompt(spec: dict) -> str:
    """카드 1장용 gpt-image-2 프롬프트. 한글 문구를 '그대로' 렌더하도록 지시."""
    ad_line = ""
    if spec["is_ad"]:
        ad_line = (
            "좌측 상단에 빨간 둥근 배지로 '광고' 라고 작게 표기. "
            "하단에 작은 회색 글씨로 '무료수신거부 080-XXX-XXXX' 표기. "
        )
    big_line = f"중앙에 매우 큰 코랄색(#e8533f) 굵은 숫자로 '{spec['big']}'. " if spec["big"] else ""

    return (
        "한국 보험설계사가 고객에게 보내는 깔끔하고 신뢰감 있는 정보형 카드뉴스. "
        "세로형, 흰 배경, 네이비(#1f3a5f)와 코랄(#e8533f) 포인트, 여백이 넉넉한 미니멀 디자인. "
        "모든 글자는 또렷한 한국어로 정확히 렌더링하고 오탈자가 없어야 함.\n\n"
        f"상단 작은 배지: '{spec['badge']}'\n"
        f"큰 제목(네이비, 굵게): '{spec['headline']}'\n"
        f"{big_line}"
        f"본문(회색): '{spec['body']}'\n"
        f"하단 연한 주황 박스 안에 말풍선 아이콘과 함께 굵은 주황 글씨: '{spec['hook']}'\n"
        f"{ad_line}"
        "사진이나 사람 얼굴 없이, 타이포그래피 중심의 카드. 광고처럼 자극적이지 않고 따뜻하고 단정하게."
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
