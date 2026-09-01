#!/usr/bin/env python3
"""최종 검수 게이트: 완성본 소리를 다시 받아 적어서 원본 대본과 맞는지 본다.

사용자에게 결과물을 넘기기 전에 클로드가 스스로 돌리는 스크립트다.
일치율이 기준 밑이면 종료 코드 1을 내고, 사용자에게 가져가지 말라고 알린다.

사용법:
  python3 qc_check.py final.mp4 script.txt [--model base]
"""
import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

PASS_RATIO = 0.85  # 이 밑으로 떨어지면 사람한테 넘기지 말고 다시 손봐야 한다


def transcribe_text(video: Path, model: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["whisper", str(video), "--model", model, "--output_format", "txt",
             "--output_dir", td, "--language", "Korean"],
            check=True,
        )
        return (Path(td) / f"{video.stem}.txt").read_text().strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("script", help="원본 대본 텍스트 파일")
    ap.add_argument("--model", default="base")
    args = ap.parse_args()

    result_text = transcribe_text(Path(args.video), args.model)
    script_text = Path(args.script).read_text().strip()

    ratio = difflib.SequenceMatcher(None, script_text, result_text).ratio()
    diff = "\n".join(difflib.unified_diff(
        script_text.split(), result_text.split(), lineterm="",
        fromfile="대본", tofile="완성본",
    ))

    print(f"일치율: {ratio:.1%}")
    if diff:
        print("--- 차이 ---")
        print(diff)

    if ratio < PASS_RATIO:
        print("\n기준 미달 — 사용자에게 넘기지 말고 다시 편집할 것", file=sys.stderr)
        sys.exit(1)
    print("\n통과 — 사용자에게 넘겨도 됨")


if __name__ == "__main__":
    main()
