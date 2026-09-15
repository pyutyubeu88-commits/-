#!/usr/bin/env python3
"""컷 편집: 재테이크(같은 말 반복) 제거는 자동, 무음 구간 트리밍은 "제안"만 한다.

재테이크 제거(같은 문장을 다시 찍은 앞쪽 테이크 삭제)는 그대로 자동 실행한다 — 이건
명백히 버릴 내용이라 사람 확인이 필요 없다고 본다.

무음 구간(문장 사이 정적) 트리밍은 더 이상 자동으로 잘라내지 않는다. 대신 후보 구간
목록(타임스탬프+길이)을 `<output>.silence_candidates.json`으로 출력해서 "이 구간들을
자를지 검토해주세요" 형태로 사람에게 넘긴다. 실제로 그 구간까지 잘라낸 결과물을 받고
싶으면 `--apply-silence-cuts`를 명시적으로 줘야 한다 — 기본값은 제안만 하고 무음은
원본 그대로 남긴다.

사용법:
  python3 cut_edit.py input.mp4 output.mp4 [--speed 1.1] [--model base]
  python3 cut_edit.py input.mp4 output.mp4 --apply-silence-cuts   # 제안된 무음까지 실제로 자름

openai-whisper CLI(pip install openai-whisper)와 ffmpeg가 설치돼 있어야 한다.
"""
import argparse
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SILENCE_GAP = 0.6  # 이 이상 비면 "무음 구간 후보"로 제안한다 (초) — 자동으로 자르지 않는다
DUP_RATIO = 0.82  # 이 유사도 이상이면 "같은 말"(재테이크)로 본다 — 이건 자동으로 자른다
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


def split_retakes(segments: list[dict]) -> tuple[list[dict], list[dict]]:
    """연속 구간 중 문장이 겹치면 이전 것을 버리고 마지막 것만 남긴다.
    (kept, dropped) 둘 다 돌려준다 — dropped는 실제로 잘라낼 재테이크 구간들."""
    kept: list[dict] = []
    dropped: list[dict] = []
    for seg in segments:
        while kept and difflib.SequenceMatcher(
            None, kept[-1]["text"].strip(), seg["text"].strip()
        ).ratio() >= DUP_RATIO:
            dropped.append(kept.pop())
        kept.append(seg)
    return kept, dropped


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def complement(cut_intervals: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    """cut_intervals(잘라낼 구간)을 제외한 나머지를 [0, duration] 안에서 돌려준다."""
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in cut_intervals:
        if s > cursor:
            keep.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        keep.append((cursor, duration))
    return keep


def find_silence_candidates(kept_segments: list[dict], duration: float) -> list[dict]:
    """재테이크 제거 후 남은(말하는) 구간들 사이의 침묵 후보를 찾는다.
    자르지 않고 후보 목록만 만든다."""
    candidates = []
    ordered = sorted(kept_segments, key=lambda s: s["start"])
    prev_end = 0.0
    for seg in ordered:
        gap_start = prev_end
        gap_end = seg["start"]
        if gap_end - gap_start >= SILENCE_GAP:
            candidates.append({
                "start": round(gap_start, 3),
                "end": round(gap_end, 3),
                "duration": round(gap_end - gap_start, 3),
            })
        prev_end = max(prev_end, seg["end"])
    if duration - prev_end >= SILENCE_GAP:
        candidates.append({
            "start": round(prev_end, 3),
            "end": round(duration, 3),
            "duration": round(duration - prev_end, 3),
        })
    return candidates


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
    video = video.resolve()
    output = output.resolve()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        part_names = []
        for i, (s, e) in enumerate(intervals):
            name = f"part_{i:04d}.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(video),
                 "-c:v", "libx264", "-c:a", "aac", "-avoid_negative_ts", "make_zero", name],
                check=True, capture_output=True, cwd=str(td_path),
            )
            part_names.append(name)

        # concat 데뮤서는 리스트 파일 '내용'에 경로를 적는데, 그 경로는 argv가 아니라서
        # ~/.local/bin/ffmpeg 래퍼의 /mnt·/home 자동 변환이 안 먹는다(실측 확인). 그래서
        # concat.txt와 파트 파일들을 같은 임시 디렉터리에 두고 cwd를 거기로 잡아
        # 순수 상대 파일명만 적는다.
        concat_list = td_path / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in part_names))
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
             "-c", "copy", "concat_out.mp4"],
            check=True, capture_output=True, cwd=str(td_path),
        )

        subprocess.run(
            ["ffmpeg", "-y", "-i", "concat_out.mp4",
             "-vf", f"setpts={1 / speed:.6f}*PTS",
             "-af", build_atempo_chain(speed),
             str(output)],
            check=True, capture_output=True, cwd=str(td_path),
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--speed", type=float, default=1.1)
    ap.add_argument("--model", default="base")
    ap.add_argument("--apply-silence-cuts", action="store_true",
                     help="제안된 무음 구간까지 실제로 잘라낸다 (기본값은 제안만 하고 무음은 남긴다)")
    args = ap.parse_args()

    video = Path(args.input)
    output = Path(args.output)
    duration = probe_duration(video)
    segments = transcribe(video, args.model)
    kept_segments, dropped_segments = split_retakes(segments)

    if not kept_segments:
        print("남길 구간이 없습니다 (자막 인식 실패 가능성)", file=sys.stderr)
        sys.exit(1)

    # 1) 재테이크는 항상 자동으로 잘라낸다.
    retake_cut_spans = merge_intervals([
        (max(0.0, seg["start"] - PAD), min(duration, seg["end"] + PAD))
        for seg in dropped_segments
    ])
    keep_intervals = complement(retake_cut_spans, duration) if retake_cut_spans else [(0.0, duration)]

    # 2) 무음 구간은 자르지 않고 후보만 뽑는다.
    silence_candidates = find_silence_candidates(kept_segments, duration)
    proposal_path = output.with_name(output.stem + ".silence_candidates.json")
    proposal_path.write_text(json.dumps(silence_candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    if silence_candidates:
        total = sum(c["duration"] for c in silence_candidates)
        print(f"무음 구간 후보 {len(silence_candidates)}개(합계 {total:.1f}s) 발견 → {proposal_path}")
        print("이 구간들을 자를지 검토해주세요. 실제로 자르려면 --apply-silence-cuts로 다시 실행할 것.")
    else:
        print("무음 구간 후보 없음.")

    # 3) --apply-silence-cuts가 있으면 승인된 것으로 보고 후보 구간도 추가로 잘라낸다.
    if args.apply_silence_cuts and silence_candidates:
        silence_spans = [(c["start"], c["end"]) for c in silence_candidates]
        all_cut_spans = merge_intervals(retake_cut_spans + silence_spans)
        keep_intervals = complement(all_cut_spans, duration)
        print(f"--apply-silence-cuts 적용 — 무음 구간 {len(silence_candidates)}개도 잘라낸다.")

    build_output(video, keep_intervals, args.speed, output)
    kept = sum(e - s for s, e in keep_intervals)
    retake_note = f", 재테이크 {len(dropped_segments)}개 제거" if dropped_segments else ""
    print(f"{duration:.1f}s → {kept:.1f}s 구간 유지{retake_note}, {args.speed}배속 적용 → {output}")


if __name__ == "__main__":
    main()
