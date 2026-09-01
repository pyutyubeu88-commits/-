#!/usr/bin/env python3
"""고정 상단 질문 배너 + 하단 로고 워터마크를 영상 처음부터 끝까지 입힌다.

레퍼런스(치과 인터뷰형 숏폼) 스타일: 흰 띠 배경 위에 "Q. + 질문 2줄"이
영상 내내 고정으로 떠 있고, 하단 좌측에 로고+서브텍스트가 고정 워터마크로 깔린다.
자막(make_captions.py)과는 별개 레이어라, 보통 순서는 컷편집 → 리프레임 → 이 스크립트
→ 자막 → qc_check.py.

사용법:
  python3 add_branding.py input.mp4 output.mp4 \
      --question "동양인과 서양인" "치아 구조가 다른가요?" \
      --logo "SMILE VIEW" "DENTAL" \
      --font /path/to/Pretendard-Bold.ttf \
      [--style ../presets/default_style.json]

한글이 들어가므로 fontfile은 한글을 지원하는 폰트여야 한다.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def write_text(td: Path, name: str, text: str) -> Path:
    p = td / name
    p.write_text(text, encoding="utf-8")
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--question", nargs=2, metavar=("LINE1", "LINE2"),
                     help="상단 고정 질문 배너 2줄 (1줄=검정, 2줄=강조색)")
    ap.add_argument("--logo", nargs=2, metavar=("LINE1", "LINE2"),
                     help="하단 좌측 로고 텍스트 2줄 (1줄=브랜드명, 2줄=서브텍스트)")
    ap.add_argument("--style", default=str(SKILL_DIR / "presets" / "default_style.json"))
    ap.add_argument("--font", required=True, help="한글 지원 폰트 파일(.ttf/.otf) 경로")
    args = ap.parse_args()

    if not args.question and not args.logo:
        raise SystemExit("--question 또는 --logo 중 하나는 있어야 한다")

    style = json.loads(Path(args.style).read_text())["branding"]

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        filters = []

        if args.question:
            label = write_text(td_path, "qlabel.txt", "Q.")
            q1 = write_text(td_path, "q1.txt", args.question[0])
            q2 = write_text(td_path, "q2.txt", args.question[1])
            filters += [
                f"drawbox=x=0:y=0:w=iw:h={style['header_height']}:color={style['header_bg']}@1:t=fill",
                (f"drawtext=fontfile={args.font}:textfile={label}:fontcolor={style['header_accent_color']}"
                 f":fontsize={style['header_label_size']}:x=(w-text_w)/2:y={style['header_label_y']}"),
                (f"drawtext=fontfile={args.font}:textfile={q1}:fontcolor={style['header_line1_color']}"
                 f":fontsize={style['header_font_size']}:x=(w-text_w)/2:y={style['header_line1_y']}"),
                (f"drawtext=fontfile={args.font}:textfile={q2}:fontcolor={style['header_accent_color']}"
                 f":fontsize={style['header_font_size']}:x=(w-text_w)/2:y={style['header_line2_y']}"),
            ]

        if args.logo:
            l1 = write_text(td_path, "l1.txt", args.logo[0])
            l2 = write_text(td_path, "l2.txt", args.logo[1])
            filters += [
                (f"drawtext=fontfile={args.font}:textfile={l1}:fontcolor={style['logo_color']}"
                 f":fontsize={style['logo_font_size']}:x={style['logo_x']}:y={style['logo_y']}"),
                (f"drawtext=fontfile={args.font}:textfile={l2}:fontcolor={style['logo_sub_color']}"
                 f":fontsize={style['logo_sub_font_size']}:x={style['logo_x']}:y={style['logo_sub_y']}"),
            ]

        subprocess.run(
            ["ffmpeg", "-y", "-i", args.input, "-vf", ",".join(filters),
             "-c:a", "copy", args.output],
            check=True,
        )
    print(f"브랜딩(질문 배너/로고) 입혀서 저장: {args.output}")


if __name__ == "__main__":
    main()
