#!/usr/bin/env python3
"""화면 그래픽: 비교 차트/트리비아 카드를 애니메이션으로 얹는다.

"스케일링 전 80% → 후 10%" 같은 걸 정적 사진 대신 막대가 자라는 인포그래픽으로
보여준다. 예전엔 "자동화 어려움"으로 파이프라인에서 뺐던 단계인데,
HyperFrames로 되살렸다.

카드는 오버레이라서 영상 길이도 음성도 안 바뀐다 (insert_broll.py처럼 구간을
잘라 끼우는 게 아니다). 그래서 자막 타이밍이 안 어긋난다.

사용법:
  python3 hyperframes_graphic.py input.mp4 output.mp4 \
      --data chart.json --at 12.5 --duration 4 \
      --font /path/to/Pretendard-Bold.ttf [--fps 30] [--keep-project ./hf_graphic]

chart.json 형식 (클로드가 대본 보고 만든다):
  {
    "title": "스케일링 전 / 후",
    "subtitle": "치석 남은 양",
    "items": [
      {"label": "스케일링 전", "value": 80, "max": 100, "suffix": "%", "color": "#8892A6"},
      {"label": "스케일링 후", "value": 10, "max": 100, "suffix": "%", "color": "#2D6CDF"}
    ],
    "note": "* 원장님 진료 기준",
    "scrim": true,
    "card_top": 520
  }

  items를 하나만 넣으면 트리비아 카드(제목 + 숫자 하나)로도 쓸 수 있다.
  색·글자 크기 기본값은 presets/default_style.json의 `motion.graphic`,
  그리고 templates/graphic.html 상단 DEFAULTS 참고.

필요: Node.js 22+, ffmpeg.
"""
import argparse
import json
import tempfile
from pathlib import Path

from hyperframes_common import (
    DEFAULT_STYLE, composite_timed, load_style,
    probe_duration, probe_wh, render_alpha_clip,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--data", required=True, help="차트 내용 JSON 경로")
    ap.add_argument("--at", type=float, required=True, help="이 시각(초)부터 카드가 뜬다")
    ap.add_argument("--duration", type=float, required=True, help="카드를 몇 초 띄울지")
    ap.add_argument("--style", default=str(DEFAULT_STYLE))
    ap.add_argument("--font", required=True, help="한글 지원 폰트 파일(.ttf/.otf) 경로")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--keep-project", default=None,
                    help="HyperFrames 프로젝트를 이 경로에 남긴다 (preview용)")
    args = ap.parse_args()

    video = Path(args.input)
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if not data.get("items"):
        raise SystemExit("chart.json에 items가 있어야 한다")

    style = load_style(args.style)
    defaults = style.get("motion", {}).get("graphic", {})
    props = {**defaults, **data}

    width, height = probe_wh(video)
    duration = probe_duration(video)
    end = args.at + args.duration
    if end > duration:
        raise SystemExit(f"--at + --duration({end:.1f}s)이 원본 길이({duration:.1f}s)를 넘는다")

    with tempfile.TemporaryDirectory() as td:
        clip = render_alpha_clip(
            "graphic.html", props, Path(td) / "graphic.mov",
            width=width, height=height, duration=args.duration,
            font=Path(args.font), fps=args.fps,
            keep_project=Path(args.keep_project) if args.keep_project else None,
        )
        composite_timed(video, [(clip, args.at, args.duration)],
                        Path(args.output), width, height)

    print(f"{args.at}s~{end:.1f}s 구간에 화면 그래픽 삽입 완료 → {args.output}")


if __name__ == "__main__":
    main()
