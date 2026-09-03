#!/usr/bin/env python3
"""
generate_caption.py
--------------------
질문 텍스트 + (선택) whisper 전사 텍스트를 바탕으로 인스타그램 게시글 캡션 + 해시태그 초안을 만든다.

의료광고법 주의 (필수 준수):
  - "완치", "최고", "1위", "부작용 없음", "100% 효과", "전후사진 과장" 등 표현 금지.
  - 정보성/일상적 톤 유지. 특정 시술의 효과를 단정하거나 환자를 유인하는 문구 금지.
  - 원장 개인 자격/전문성 언급은 사실 범위 내에서만.

파이프라인 순서: 컷편집 → 리프레임 → 브랜딩 → B-roll → 화면 그래픽 → 효과음 → 자막 →
자막 강조 모션 → **인스타 캡션 생성** → QC. (make_captions.py 다음, qc_check.py 앞)

사용법:
  python3 generate_caption.py --question "..." --answer-text "..." --out caption.txt
"""
from __future__ import annotations

import argparse
import re

CLINIC_NAME = "스마일뷰치과"
CLINIC_HANDLE_HINT = "신논현역 치과"

# 의료광고법 저촉 소지가 있어 자동 생성 문구에 절대 넣지 않는 표현
BANNED_PHRASES = [
    "완치", "최고", "1위", "no.1", "No.1", "부작용 없", "100% 효과", "100%효과",
    "무통증", "전혀 안 아", "가장 잘", "국내 최초", "유일", "보장", "즉시 효과",
]


def _sanitize(text: str) -> str:
    """혹시 모를 금칙 표현이 섞여 들어오면 제거(안전장치)."""
    out = text
    for phrase in BANNED_PHRASES:
        out = out.replace(phrase, "")
    return out


def _default_hashtags() -> list[str]:
    return [
        "#스마일뷰치과", "#신논현치과", "#신논현역치과", "#강남치과",
        "#치과상식", "#치아건강", "#치과Q&A", "#원장님답변",
        "#논현동치과", "#치과추천보다정보",
    ]


def build_caption(question: str, answer_summary: str | None = None) -> str:
    """
    question: 촬영 시 사용한 질문 텍스트 (예: "동양인과 서양인 치아 구조가 다른가요?")
    answer_summary: whisper 전사 원문(선택) - 있으면 도입부에 자연스럽게 녹여 넣음.
                     없어도 질문만으로 캡션 초안 생성 가능.
    """
    question = _sanitize(question.strip())

    intro_lines = [
        f"Q. {question}",
        "",
        f"{CLINIC_NAME} 김한결 원장님이 답해드렸어요.",
    ]

    if answer_summary:
        # 전사 원문은 구어체라 그대로 쓰지 않고, 과도한 단정 표현만 제거해 요약 톤으로 소개
        summary = _sanitize(answer_summary.strip())
        summary = re.sub(r"\s+", " ", summary)
        if len(summary) > 120:
            summary = summary[:117].rstrip() + "…"
        intro_lines.append("")
        intro_lines.append(f"👉 영상에서 자세한 설명 확인해보세요. \"{summary}\"")

    intro_lines += [
        "",
        "궁금한 치아/치과 관련 질문은 댓글로 남겨주시면",
        "다음 Q&A 영상에서 다뤄드릴게요 🦷",
        "",
        f"📍 {CLINIC_HANDLE_HINT} | 진료 상담 문의는 프로필 링크 확인",
        "",
        " ".join(_default_hashtags()),
    ]

    caption = "\n".join(intro_lines)
    return _sanitize(caption)


def main():
    ap = argparse.ArgumentParser(description="인스타 캡션/해시태그 초안 생성")
    ap.add_argument("--question", required=True, help="촬영 시 사용한 질문 텍스트")
    ap.add_argument("--answer-text", default=None, help="whisper 전사 원문(선택)")
    ap.add_argument("--out", default=None, help="저장할 .txt 경로 (생략 시 stdout 출력)")
    args = ap.parse_args()

    caption = build_caption(args.question, args.answer_text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(caption + "\n")
        print(f"caption saved -> {args.out}")
    else:
        print(caption)


if __name__ == "__main__":
    main()
