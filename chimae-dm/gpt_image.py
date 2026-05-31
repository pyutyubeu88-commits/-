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


# ── 일자별 3D 캐릭터/비주얼 모티프 (wonder 카드뉴스 스타일) ──
# 사용자가 직접 검증한 고퀄 결과물 수준 — 3D 렌더 캐릭터 + 인포그래픽 요소.
MOTIF = {
    1: "햇살 드는 창가에 김이 오르는 따뜻한 차 한 잔과 작은 화분. "
       "포근하고 평온한 3D 렌더 스타일 일러스트를 상단에 크게.",
    2: "서로 마주 보며 환하게 웃는 노년 부모님 3D 캐릭터(엄마·아빠)가 손을 흔드는 모습. "
       "친근하고 따뜻한 픽사풍 3D 렌더.",
    3: "걱정스러운 표정으로 생각하는 중년 자녀 3D 캐릭터와 지갑/동전 아이콘. "
       "경제적 부담을 상징하는 따뜻한 3D 렌더.",
    4: "손바닥 위에 뇌 모형을 올려 든 중년 남성 3D 캐릭터. "
       "신약·치료를 상징하는 깔끔한 3D 렌더, 한쪽에 휠체어를 탄 어르신과 돌보는 가족.",
    5: "금이 가거나 일부가 비어 있는 방패를 든 사람 3D 캐릭터. "
       "‘보장의 빈틈’을 직관적으로 보여주는 3D 렌더.",
    6: "튼튼한 우산/방패로 가족을 감싸 보호하는 안정감 있는 3D 캐릭터. "
       "단계별 보장을 상징하는 연결된 체크 아이콘.",
    7: "편안하게 마주 앉아 상담하는 설계사와 고객 3D 캐릭터, 따뜻한 대화 분위기. "
       "악수 또는 미소.",
}

# 일자별 데이터 블록 (통계 카드 — 큰 % + 설명 + 출처). 없으면 일반 본문.
DATA_BLOCKS = {
    2: {
        "section": "자녀도 부모의 치매를 두려워한다?",
        "stats": [
            ("64.6%", "나는 부모님이 인지장애(치매)가 생기는 것에 대한 걱정이 있다"),
            ("58.1%", "내 부모님이 중증에 걸리는 것보다 인지장애(치매)에 걸리는 것이 더 두렵다"),
        ],
        "source": "출처: 트렌드모니터, 엠브레인 2025",
        "close": "자녀 상당수가 부모의 치매 발생에 대해 걱정과 두려움을 갖고 있습니다.",
    },
    3: {
        "section": "치매, 준비된 사람은 22.4%뿐",
        "stats": [
            ("65.5%", "부모님 인지장애(치매)가 오면 나의 경제적 상황이 크게 어려워질 것 같다"),
            ("22.4%", "부모님이 인지장애(치매)가 생기는 것에 대해 대비하고 있다"),
        ],
        "source": "출처: 트렌드모니터, 엠브레인 2025",
        "close": "이제 한발 앞선 대비로 나와 가족의 미래를 지켜나가세요.",
    },
    4: {
        "section": "치매 치료제, 레켐비란?",
        "rows": [
            ("사용대상", "초기 알츠하이머 환자(경도인지장애 포함) — 진행된 상태에선 효과 제한적"),
            ("투여방식", "병원에서 정맥주사(IV)로 정기적으로 맞는 치료"),
            ("기대효과", "완치가 아닌 인지 기능 저하 속도를 약 27% 늦춤"),
            ("비용", "18개월(36회) 약 6,480만 원 · 대부분 비급여"),
        ],
        "source": "약품명: 레켐비(Leqembi) · 정확 표기 주의",
        "close": "만약의 순간에도 후회 없이 치료받으려면 지금부터의 준비가 필수입니다.",
    },
}


def _data_block_lines(spec: dict) -> str:
    """데이터 블록이 있는 날은 wonder 스타일 인포그래픽 지시를 추가."""
    db = DATA_BLOCKS.get(spec["day"])
    if not db:
        return ""
    out = (
        f"\n[데이터 인포그래픽 섹션]\n"
        f"· 가로 색상 헤더 바(딥 네이비 또는 그린 배경에 흰 글씨)에 섹션 제목: '{db['section']}'\n"
    )
    if "stats" in db:
        out += "· 아래 통계를 '큰 롯데 레드 퍼센트 숫자 + 옆에 설명문' 형태로 정확히 배치:\n"
        for pct, desc in db["stats"]:
            out += f"   - '{pct}'  →  '{desc}'\n"
    if "rows" in db:
        out += "· 아래 항목을 '아이콘 + 라벨 + 설명' 리스트(연한 박스)로 정확히 배치:\n"
        for label, desc in db["rows"]:
            out += f"   - [{label}]  {desc}\n"
    out += f"· 작은 회색 글씨 출처: '{db['source']}'\n"
    out += f"· 하단에 형광펜(노랑/연두) 강조 처리된 마무리 문장: '{db['close']}'\n"
    return out


def build_prompt(spec: dict) -> str:
    """카드 1장용 gpt-image-2 프롬프트 — wonder 카드뉴스급 인포그래픽 스타일."""
    ad_line = ""
    if spec["is_ad"]:
        ad_line = (
            "· 좌측 상단에 작고 단정한 빨간 둥근 배지로 '광고' 표기. "
            "맨 하단에 작은 회색 글씨로 '무료수신거부 080-XXX-XXXX' 표기.\n"
        )
    big_line = (
        f"· 중앙에 매우 큰 롯데 레드(#DA291C) 초굵은 숫자로 '{spec['big']}' "
        "(입체감 있게, 정확히 렌더).\n"
        if spec["big"] else ""
    )
    motif = MOTIF.get(spec["day"], "")
    data_section = _data_block_lines(spec)

    return (
        # ── 스타일/품질 지시 (wonder 카드뉴스 = 사용자 검증 고퀄 기준) ──
        "한국 보험사 공식 SNS 카드뉴스 수준의 프리미엄 인포그래픽 1장. 세로형(1024x1536). "
        "전체 톤: 깔끔한 연한 피치/아이보리 배경 위에 흰색 둥근 카드 패널들이 층층이 쌓인 "
        "정보 풍부한 인포그래픽. 픽사풍 3D 렌더 캐릭터로 따뜻함을, 색상 헤더 바와 큰 숫자로 "
        "신뢰감을 준다. 시그니처 컬러는 롯데 레드(#DA291C), 보조로 딥 네이비와 차분한 그린. "
        "본문은 가독성 높은 딥 그레이(#2b2b2b). 모든 한국어 텍스트는 오탈자 없이 100% 정확히 "
        "렌더링(글자 깨짐·누락 절대 금지).\n\n"
        # ── 레이아웃 골격 ──
        "[레이아웃]\n"
        f"· 좌측 상단: 둥근 탭 형태의 작은 섹션 라벨 '{spec['badge']}'\n"
        "· 우측 상단: 소문자 산세리프 워드마크 'wonder' (롯데손해보험 콘텐츠 브랜드 톤)\n"
        f"· 메인 헤드라인(매우 굵게, 일부 단어는 롯데 레드 강조): '{spec['headline']}'\n"
        f"· 헤드라인 옆/위에 주제에 맞는 3D 캐릭터: {motif}\n"
        f"{big_line}"
        f"· 본문 설명(딥 그레이): '{spec['body']}'\n"
        f"{data_section}"
        f"· 하단 둥근 연한 레드 박스 안, 말풍선 아이콘과 굵은 롯데 레드 글씨로 질문: '{spec['hook']}'\n"
        f"· 맨 하단: 좌측에 작은 회색 글씨 '롯데손해보험', 우측에 '{AGENT_NAME} {AGENT_TEL}'\n"
        f"{ad_line}"
        "\n전체적으로 정보가 빽빽하되 정돈된, '진짜 보험사 공식 카드뉴스'처럼 완성도 높게. "
        "실사 사진·사람 얼굴 클로즈업은 쓰지 말고 3D 일러스트로."
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
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    OUT.mkdir(exist_ok=True)
    client = OpenAI()
    specs = card.card_specs()
    print(f"gpt-image-2 로 {len(specs)}장 '동시' 생성 시작 (size={SIZE}, quality={QUALITY})")
    t0 = time.time()

    def _one(s):
        p = OUT / f"gptcard_day{s['day']}.png"
        generate_card(client, s, p)
        return s["day"], p

    # 7장을 동시에 요청 → 순차 대비 대폭 단축
    with ThreadPoolExecutor(max_workers=len(specs)) as ex:
        futures = {ex.submit(_one, s): s for s in specs}
        for fut in as_completed(futures):
            day, p = fut.result()
            print(f"  ✅ {day}일차 → {p}  ({time.time()-t0:.0f}초 경과)")

    print(f"완료. 총 {time.time()-t0:.0f}초. out_gpt/ 확인")


if __name__ == "__main__":
    main()
