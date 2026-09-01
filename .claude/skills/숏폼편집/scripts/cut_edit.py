#!/usr/bin/env python3
"""컷 편집: 무음 구간 + 재테이크(같은 말 반복) 제거, 배속 적용.

사용법:
  python3 cut_edit.py input.mp4 output.mp4 [--speed 1.1] [--model base]

openai-whisper CLI(pip install openai-whisper)와 ffmpeg가 설치돼 있어야 한다.
"""
import argparse
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SILENCE_GAP = 0.6  # 이 이상 비면 무음 구간으로 잘라낸다 (초)
DUP_RATIO = 0.82  # 이 유사도 이상이면 "같은 말"로 본다
PAD = 0.08  # 컷 경계에 붙이는 여유 (초), 숨소리 잘림 방지


def transcribe(video: Path, model: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["whisper", str(video), "--model", model, "--output_format", "json",
             "--output_dir", td, "--language", "Korean"],
            check=True,
        )
        data = json.loads((Path(td) / f"{video.stem}.json").read_text())
    return data["segments"]


def drop_retakes(segments: list[dict]) -> list[dict]:
    """연속 구간 중 문장이 겹치면 이전 것을 버리고 마지막 것만 남긴다."""
    kept: list[dict] = []
    for seg in segments:
        while kept and difflib.SequenceMatcher(
            None, kept[-1]["text"].strip(), seg["text"].strip()
        ).ratio() >= DUP_RATIO:
            kept.pop()
        kept.append(seg)
    return kept


def to_intervals(segments: list[dict], duration: float) -> list[tuple[float, float]]:
    """말하는 구간만 남기고, 붙어 있는 구간은 하나로 합친다."""
    intervals: list[tuple[float, float]] = []
    for seg in segments:
        start = max(0.0, seg["start"] - PAD)
        end = min(duration, seg["end"] + PAD)
        if intervals and start - intervals[-1][1] < SILENCE_GAP:
            intervals[-1] = (intervals[-1][0], end)
        else:
            intervals.append((start, end))
    return intervals


def probe_duration(video: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def build_atempo_chain(speed: float) -> str:
    """ffmpeg atempo 필터는 0.5~2.0 배속만 받는다."""
    if not 0.5 <= speed <= 2.0:
        raise ValueError("speed는 0.5~2.0 사이만 지원한다")
    return f"atempo={speed:.4f}"


def build_output(video: Path, intervals: list[tuple[float, float]], speed: float, output: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, (s, e) in enumerate(intervals):
            part = Path(td) / f"part_{i:04d}.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(video),
                 "-c:v", "libx264", "-c:a", "aac", "-avoid_negative_ts", "make_zero", str(part)],
                check=True, capture_output=True,
            )
            parts.append(part)

        concat_list = Path(td) / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in parts))
        concat_out = Path(td) / "concat.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(concat_out)],
            check=True, capture_output=True,
        )

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(concat_out),
             "-vf", f"setpts={1 / speed:.6f}*PTS",
             "-af", build_atempo_chain(speed),
             str(output)],
            check=True, capture_output=True,
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--speed", type=float, default=1.1)
    ap.add_argument("--model", default="base")
    args = ap.parse_args()

    video = Path(args.input)
    duration = probe_duration(video)
    segments = drop_retakes(transcribe(video, args.model))
    intervals = to_intervals(segments, duration)

    if not intervals:
        print("남길 구간이 없습니다 (자막 인식 실패 가능성)", file=sys.stderr)
        sys.exit(1)

    build_output(video, intervals, args.speed, Path(args.output))
    kept = sum(e - s for s, e in intervals)
    print(f"{duration:.1f}s → {kept:.1f}s 구간 유지, {args.speed}배속 적용 → {args.output}")


if __name__ == "__main__":
    main()
