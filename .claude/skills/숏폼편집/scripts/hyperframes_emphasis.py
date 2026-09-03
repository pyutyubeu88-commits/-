#!/usr/bin/env python3
"""자막 강조를 '그려지는' 모션으로 바꾼다 (make_captions.py의 `**` 확대를 대체).

make_captions.py는 강조 구간을 ASS `\\fscx\\fscy`로 글자만 키운다. 이 스크립트는
그 위에 밑줄이 좌→우로 그어지거나 형광펜이 칠해지는 애니메이션을 얹는다.
글자는 다시 그리지 않으므로 자막이 겹쳐 보이지 않는다.

**반드시 make_captions.py 다음에, qc_check.py 앞에서 돌린다.**
오버레이만 얹는 거라 영상 길이도 음성도 안 바뀐다 — 자막 타이밍이 안 어긋난다.

사용법:
  python3 hyperframes_emphasis.py input.mp4 output.mp4 \
      --cues cues.json --font /path/to/Pretendard-Bold.ttf \
      [--style ../presets/default_style.json] [--fps 30] [--keep-project ./hf_emph]

cues.json 형식 (강조할 대사와 그 대사가 화면에 떠 있는 구간 — 클로드가 대본/자막 보고 만든다):
  [
    {"text": "많이 다릅니다", "start": 3.2, "end": 5.0},
    {"text": "6개월에 한 번", "start": 18.4, "end": 20.1, "mode": "highlight"}
  ]

  mode: "underline"(기본, 글자를 안 가린다) 또는 "highlight"(형광펜 느낌, 반투명)
  color / thickness / gap 을 큐마다 따로 줄 수도 있다.

주의: 선 길이는 `text`를 자막과 같은 폰트·크기로 재서 맞춘다. 그래서
      default_style.json의 `korean_size`, `korean_margin_v`, 그리고 --font가
      실제 자막과 같아야 위치가 맞는다. 밑줄을 쓸 거면 `emphasis_scale`을 100으로
      두는 게 깔끔하다 (글자가 커지면 잰 폭과 어긋난다).

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
    ap.add_argument("--cues", required=True)
    ap.add_argument("--style", default=str(DEFAULT_STYLE))
    ap.add_argument("--font", required=True, help="자막에 쓴 것과 같은 폰트 파일 경로")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--keep-project", default=None,
                    help="마지막 큐의 HyperFrames 프로젝트를 이 경로에 남긴다 (preview용)")
    args = ap.parse_args()

    video = Path(args.input)
    cues = json.loads(Path(args.cues).read_text(encoding="utf-8"))
    if not cues:
        raise SystemExit("cues.json이 비어 있다")

    style = load_style(args.style)
    motion = style.get("motion", {}).get("emphasis", {})
    width, height = probe_wh(video)
    duration = probe_duration(video)

    for cue in cues:
        if cue["end"] <= cue["start"]:
            raise SystemExit(f"end가 start보다 뒤여야 한다: {cue}")
        if cue["end"] > duration + 0.05:
            raise SystemExit(f"큐가 영상 길이({duration:.1f}s)를 넘는다: {cue}")

    with tempfile.TemporaryDirectory() as td:
        clips: list[tuple[Path, float, float]] = []
        for i, cue in enumerate(cues):
            span = cue["end"] - cue["start"]
            props = {
                "text": cue["text"],
                "mode": cue.get("mode", motion.get("mode", "underline")),
                "font_size": cue.get("font_size", style["korean_size"]),
                "line_bottom": cue.get("line_bottom", style["korean_margin_v"]),
                "color": cue.get("color", motion.get("color", "#FFE14D")),
                "thickness": cue.get("thickness", motion.get("thickness", 12)),
                "gap": cue.get("gap", motion.get("gap", 10)),
                "pad_x": cue.get("pad_x", motion.get("pad_x", 14)),
                "radius": cue.get("radius", motion.get("radius", 6)),
                "opacity": cue.get("opacity", motion.get("opacity", 1)),
                "anim": {
                    "draw": cue.get("draw", motion.get("draw", 0.38)),
                    "delay": cue.get("delay", motion.get("delay", 0.06)),
                },
            }
            keep = Path(args.keep_project) if (args.keep_project and i == len(cues) - 1) else None
            clip = render_alpha_clip(
                "emphasis.html", props, Path(td) / f"emph{i}.mov",
                width=width, height=height, duration=span,
                font=Path(args.font), fps=args.fps, keep_project=keep,
            )
            clips.append((clip, cue["start"], span))

        composite_timed(video, clips, Path(args.output), width, height)

    print(f"자막 강조 모션 {len(cues)}개 입혀서 저장: {args.output}")


if __name__ == "__main__":
    main()
