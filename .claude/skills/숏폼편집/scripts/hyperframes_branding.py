#!/usr/bin/env python3
"""상단 질문 배너 + 로고 워터마크를 '움직이게' 입힌다 (add_branding.py의 모션 버전).

add_branding.py는 ffmpeg drawtext로 정적으로 번인한다. 이 스크립트는 같은
`presets/default_style.json`의 `branding` 값을 그대로 읽어서, HyperFrames로
배너가 위에서 내려오고 로고가 좌→우로 닦이며 등장하는 애니메이션을 만든 뒤
알파 채널 클립으로 원본 위에 얹는다. 위치·색·글자 크기는 정적 버전과 같다.

정적 버전을 대체하지 않는다 — Node.js가 없는 환경에서는 add_branding.py를 계속 쓴다.

사용법(플래그는 add_branding.py와 똑같다):
  python3 hyperframes_branding.py input.mp4 output.mp4 \
      --question "동양인과 서양인" "치아 구조가 다른가요?" \
      --logo "SMILE VIEW" "DENTAL" \
      --font /path/to/Pretendard-Bold.ttf \
      [--style ../presets/default_style.json] [--anim-duration 2.0] [--fps 30]
      [--keep-project ./hf_banner]

--anim-duration: 등장 애니메이션 구간만 렌더하고 그 뒤는 마지막 프레임을 영상 끝까지
                 붙잡아 둔다(배너는 원래 끝까지 고정이라 결과가 같다). 40초짜리를 통째로
                 렌더하는 것보다 20배쯤 빠르다. 애니메이션이 잘리면 값을 키운다.
--keep-project:  생성한 HyperFrames 프로젝트를 남긴다. 그 폴더에서
                 `npx hyperframes preview`로 브라우저에서 실시간으로 손볼 수 있다.

필요: Node.js 22+ (없으면 add_branding.py를 쓰라고 안내하고 멈춘다), ffmpeg.
"""
import argparse
import tempfile
from pathlib import Path

from hyperframes_common import (
    DEFAULT_STYLE, composite_hold, css_color, css_px, load_style,
    probe_duration, probe_wh, render_alpha_clip,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--question", nargs=2, metavar=("LINE1", "LINE2"),
                    help="상단 질문 배너 2줄 (1줄=검정, 2줄=강조색)")
    ap.add_argument("--logo", nargs=2, metavar=("LINE1", "LINE2"),
                    help="하단 좌측 로고 텍스트 2줄 (1줄=브랜드명, 2줄=서브텍스트)")
    ap.add_argument("--style", default=str(DEFAULT_STYLE))
    ap.add_argument("--font", required=True, help="한글 지원 폰트 파일(.ttf/.otf) 경로")
    ap.add_argument("--anim-duration", type=float, default=2.0,
                    help="등장 애니메이션 길이(초). 이 뒤로는 마지막 프레임 고정")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--keep-project", default=None,
                    help="HyperFrames 프로젝트를 이 경로에 남긴다 (preview용)")
    args = ap.parse_args()

    if not args.question and not args.logo:
        raise SystemExit("--question 또는 --logo 중 하나는 있어야 한다")

    video = Path(args.input)
    style = load_style(args.style)
    branding = style["branding"]
    motion = style.get("motion", {}).get("branding", {})

    width, height = probe_wh(video)
    duration = probe_duration(video)
    anim = min(args.anim_duration, duration)

    props = {
        "question": list(args.question) if args.question else [],
        "logo": list(args.logo) if args.logo else [],
        "label": branding.get("header_label", "Q."),
        "header": {
            "height": branding["header_height"],
            "bg": css_color(branding["header_bg"]),
            "accent": css_color(branding["header_accent_color"]),
            "line1_color": css_color(branding["header_line1_color"]),
            "font_size": branding["header_font_size"],
            "label_size": branding["header_label_size"],
            "label_top": css_px(branding["header_label_y"], height),
            "line1_top": css_px(branding["header_line1_y"], height),
            "line2_top": css_px(branding["header_line2_y"], height),
        },
        "logo_box": {
            "left": css_px(branding["logo_x"], width),
            "top": css_px(branding["logo_y"], height),
            "color": css_color(branding["logo_color"]),
            "font_size": branding["logo_font_size"],
            "sub_color": css_color(branding["logo_sub_color"]),
            "sub_font_size": branding["logo_sub_font_size"],
            "sub_top": css_px(branding["logo_sub_y"], height),
        },
        "anim": {
            "banner_in": motion.get("banner_in", 0.55),
            "banner_delay": motion.get("banner_delay", 0.0),
            "line_in": motion.get("line_in", 0.45),
            "label_delay": motion.get("label_delay", 0.20),
            "line1_delay": motion.get("line1_delay", 0.28),
            "line2_delay": motion.get("line2_delay", 0.40),
            "logo_in": motion.get("logo_in", 0.55),
            "logo_delay": motion.get("logo_delay", 0.75),
        },
    }

    with tempfile.TemporaryDirectory() as td:
        clip = render_alpha_clip(
            "banner.html", props, Path(td) / "banner.mov",
            width=width, height=height, duration=anim,
            font=Path(args.font), fps=args.fps,
            keep_project=Path(args.keep_project) if args.keep_project else None,
        )
        composite_hold(video, clip, Path(args.output), width, height, duration)

    print(f"모션 배너/로고 입혀서 저장: {args.output}")


if __name__ == "__main__":
    main()
