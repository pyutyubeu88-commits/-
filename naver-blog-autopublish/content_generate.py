#!/usr/bin/env python3
"""
네이버 블로그용 콘텐츠 생성기 — Claude API로 제목+본문+이미지 프롬프트 생성

사용법:
    python content_generate.py "역삼동 태권도장 여름방학 특강"

결과는 drafts/<타임스탬프>.json 에 저장되며, auto_publish.py 가 이 파일을 읽어
네이버 블로그에 임시저장/발행한다.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────
# 모델은 claude-sonnet-5 고정 기본값, 필요 시 ANTHROPIC_MODEL 환경변수로 오버라이드
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
DRAFTS_DIR = Path(__file__).parent / "drafts"

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "블로그 글 제목 (후킹 강한 반말체, 이모지 적당히)"},
        "paragraphs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "본문 문단 리스트. 문단 하나가 SmartEditor 한 블록에 대응",
        },
        "image_prompts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "본문에 어울리는 이미지 생성/검색용 프롬프트 리스트 (영문)",
        },
    },
    "required": ["title", "paragraphs", "image_prompts"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """당신은 강남구 소상공인 전용 네이버 블로그 콘텐츠 작가입니다.
독자는 강남구(특히 역삼동) 지역 주민과 잠재 고객입니다.
말투는 친근하고 후킹 강한 반말체를 기본으로 하되, 정보는 정확해야 합니다.
콘텐츠 우선순위: 후킹(첫 문단) → 정보 정확성 → 저장/방문 유도.
과장 광고나 확인되지 않은 효능 주장은 하지 않습니다."""


def generate_content(topic: str) -> dict:
    client = anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    f"주제: {topic}\n\n"
                    "이 주제로 네이버 블로그 글을 작성해줘. "
                    "제목 1개, 본문 문단 5~8개, 문단별로 어울리는 이미지 프롬프트를 함께 만들어줘."
                ),
            }
        ],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude가 콘텐츠 생성을 거부했습니다. 주제를 다시 확인하세요.")

    text_block = next((b for b in response.content if b.type == "text"), None)
    if text_block is None:
        raise RuntimeError("응답에서 텍스트 블록을 찾을 수 없습니다.")

    return json.loads(text_block.text)


def save_draft(topic: str, content: dict) -> Path:
    DRAFTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = DRAFTS_DIR / f"{timestamp}.json"

    payload = {
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "model": MODEL,
        **content,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    if len(sys.argv) < 2:
        print('사용법: python content_generate.py "주제"')
        return 1

    topic = sys.argv[1]

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[오류] ANTHROPIC_API_KEY 환경변수가 없습니다. .env 파일을 확인하세요.")
        return 1

    print(f"주제 '{topic}' 로 콘텐츠 생성 중... (모델: {MODEL})")
    content = generate_content(topic)
    out_path = save_draft(topic, content)

    print(f"[완료] 초안 저장: {out_path}")
    print(f"제목: {content['title']}")
    print(f"문단 수: {len(content['paragraphs'])}, 이미지 프롬프트 수: {len(content['image_prompts'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
