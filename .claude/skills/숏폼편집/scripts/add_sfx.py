#!/usr/bin/env python3
"""효과음 합성: 무료 SFX 파일들을 지정한 타이밍에 목소리보다 작게 깔아준다.

효과음을 AI로 생성하지 않고, 무료 라이브러리(Pixabay Sound Effects, Mixkit —
둘 다 상업적 이용 무료, 저작권 표시 불필요)에서 받은 파일을 쓴다.

사용법:
  python3 add_sfx.py input.mp4 output.mp4 --cues cues.json [--default-gain -14]

cues.json 형식 (자막 뜨는 타이밍에 맞춰 클로드가 만든다):
  [
    {"time": 3.2, "file": "sfx/pop.mp3", "gain_db": -14},
    {"time": 7.8, "file": "sfx/whoosh.mp3"}
  ]
"""
import argparse
import json
from pathlib import Path
import subprocess


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--cues", required=True)
    ap.add_argument("--default-gain", type=float, default=-14.0)
    args = ap.parse_args()

    cues = json.loads(Path(args.cues).read_text())
    if not cues:
        raise SystemExit("cues.json이 비어 있다")

    inputs = ["-i", args.input]
    filter_parts = []
    mix_labels = ["[0:a]"]
    for i, cue in enumerate(cues):
        inputs += ["-i", cue["file"]]
        gain = cue.get("gain_db", args.default_gain)
        delay_ms = int(cue["time"] * 1000)
        label = f"[sfx{i}]"
        # all=1: 효과음 파일이 모노든 스테레오든 채널 수 상관없이 지연 적용
        filter_parts.append(f"[{i + 1}:a]volume={gain}dB,adelay={delay_ms}:all=1{label}")
        mix_labels.append(label)

    filter_parts.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=0[aout]"
    )

    subprocess.run(
        ["ffmpeg", "-y", *inputs,
         "-filter_complex", ";".join(filter_parts),
         "-map", "0:v", "-map", "[aout]",
         "-c:v", "copy", args.output],
        check=True,
    )
    print(f"효과음 {len(cues)}개 합성 완료 → {args.output}")


if __name__ == "__main__":
    main()
