#!/usr/bin/env python3
"""빈 장면(대사에 맞는 컷이 없는 구간)에 B-roll을 끼워 넣는다.

AI로 장면을 생성하는 대신, 직접 찍었거나 무료 스톡(Pexels, Pixabay Videos, Coverr —
전부 상업적 이용 무료)에서 받은 클립을 지정 구간에 덮어씌운다. 영상만 바뀌고
원본 음성(나레이션)은 안 끊기며, 전체 길이도 늘어나지 않는다.

사용법:
  python3 insert_broll.py main.mp4 broll.mp4 output.mp4 --at 12.5 --duration 4
"""
import argparse
import subprocess
from pathlib import Path


def probe_wh(video: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    )
    w, h = out.stdout.strip().split(",")
    return int(w), int(h)


def probe_duration(video: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("main_video")
    ap.add_argument("broll")
    ap.add_argument("output")
    ap.add_argument("--at", type=float, required=True, help="이 시각(초)부터 B-roll로 바뀐다")
    ap.add_argument("--duration", type=float, required=True, help="B-roll을 몇 초 보여줄지")
    args = ap.parse_args()

    main_video = Path(args.main_video)
    duration = probe_duration(main_video)
    w, h = probe_wh(main_video)
    end = args.at + args.duration
    if end > duration:
        raise SystemExit(f"--at + --duration({end:.1f}s)이 원본 길이({duration:.1f}s)를 넘는다")

    filter_complex = (
        f"[0:v]trim=0:{args.at:.3f},setpts=PTS-STARTPTS[v1];"
        f"[1:v]trim=0:{args.duration:.3f},setpts=PTS-STARTPTS,"
        f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[vb];"
        f"[0:v]trim={end:.3f}:{duration:.3f},setpts=PTS-STARTPTS[v2];"
        f"[v1][vb][v2]concat=n=3:v=1:a=0[vout]"
    )

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(main_video), "-i", args.broll,
         "-filter_complex", filter_complex,
         "-map", "[vout]", "-map", "0:a",
         "-c:a", "copy", args.output],
        check=True,
    )
    print(f"{args.at}s~{end:.1f}s 구간에 B-roll 삽입 완료 → {args.output}")


if __name__ == "__main__":
    main()
