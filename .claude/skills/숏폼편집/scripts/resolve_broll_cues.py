#!/usr/bin/env python3
"""B-roll 큐시트를 whisper word-timestamp와 대조해 --at/--duration을 자동으로 찾고,
insert_broll.py의 기존 스왑 로직을 그 타임스탬프에 순서대로 실행한다.

`insert_broll.py --at/--duration`(사람이 초 단위를 직접 넣는 방식)은 그대로 둔다.
이 스크립트는 그 위에 얹는 새 모드다: 대본 작성자가 whisper 전사 결과에서 그대로
복사한 문구로 큐를 적으면, 그 문구가 실제로 어느 타이밍에 나오는지 여기서 찾아준다.

매칭 방식: **정확 부분문자열 매칭만** 쓴다(공백·문장부호 정규화까지만 허용, 퍼지매칭 없음).
큐 문구가 전사 텍스트 어디에도 정확히 안 나오면 그 즉시 에러를 던지고 멈춘다 —
엉뚱한 타이밍에 B-roll이 잘못 꽂히는 걸 막는 안전장치다. 이럴 땐 큐 문구를 whisper
전사 결과(--whisper-json)에서 실제로 복사해 넣거나, insert_broll.py를 --at/--duration으로
직접 호출해서 사람이 타이밍을 수동 지정해야 한다.

cues 파일 형식 (JSON 배열):
  [
    {"phrase": "동양인과 서양인은 치아 구조가", "broll": "broll/teeth_closeup.mp4", "duration": 3.0},
    {"phrase": "실제로 많이 다릅니다", "broll": "broll/xray.mp4", "duration": 2.5}
  ]

사용법:
  python3 resolve_broll_cues.py main.mp4 output.mp4 \
      --cue-file cues.json --whisper-json whisper_word_timestamps.json

  # whisper JSON이 아직 없으면 이 스크립트가 whisper로 직접 전사한다:
  python3 resolve_broll_cues.py main.mp4 output.mp4 --cue-file cues.json --model base
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def normalize(text: str) -> str:
    """공백·문장부호만 정규화한다 — 그 외 표기(자모, 띄어쓰기 스타일 등)는 안 건드린다.
    퍼지매칭이 아니라 '정확히 같은 문구인지'를 문장부호/공백 차이 때문에 실패하지 않게
    하기 위한 최소한의 정규화다."""
    text = re.sub(r"[.,!?…\"'“”‘’]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_whisper_words(whisper_json_path: Path) -> list[dict]:
    data = json.loads(whisper_json_path.read_text(encoding="utf-8"))
    words: list[dict] = []
    for seg in data.get("segments", []):
        seg_words = seg.get("words")
        if seg_words:
            for w in seg_words:
                text = w.get("word", "")
                if text.strip():
                    words.append({"text": text, "start": float(w["start"]), "end": float(w["end"])})
        else:
            # word-level 타임스탬프가 없는 세그먼트뿐이면 세그먼트 단위로라도 매칭할 수 있게 둔다.
            text = seg.get("text", "")
            if text.strip():
                words.append({"text": text, "start": float(seg["start"]), "end": float(seg["end"])})
    return words


def transcribe_words(video: Path, model: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["whisper", str(video), "--model", model, "--output_format", "json",
             "--output_dir", td, "--language", "Korean", "--word_timestamps", "True"],
            check=True,
        )
        data = json.loads((Path(td) / f"{video.stem}.json").read_text())
    words: list[dict] = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            text = w.get("word", "")
            if text.strip():
                words.append({"text": text, "start": float(w["start"]), "end": float(w["end"])})
    return words


def find_phrase_start(phrase: str, words: list[dict]) -> float:
    """words를 이어붙인 정규화 텍스트에서 phrase(정규화)를 정확 부분문자열로 찾고,
    그 시작 지점에 해당하는 원본 단어의 start 타임스탬프를 돌려준다.
    매칭 실패 시 즉시 예외를 던진다 — 조용히 넘어가지 않는다."""
    norm_phrase = normalize(phrase)
    if not norm_phrase:
        raise ValueError(f"큐 문구가 비어 있다: {phrase!r}")

    # 각 단어의 정규화 텍스트와, 이어붙인 문자열에서 그 단어가 시작하는 offset을 같이 기록한다.
    joined = ""
    offsets: list[tuple[int, dict]] = []  # (offset_in_joined, word_dict)
    for w in words:
        norm_w = normalize(w["text"])
        if not norm_w:
            continue
        if joined:
            joined += " "
        offsets.append((len(joined), w))
        joined += norm_w

    idx = joined.find(norm_phrase)
    if idx == -1:
        raise SystemExit(
            f"B-roll 큐 매칭 실패 — 전사 텍스트에서 정확히 찾을 수 없다: {phrase!r}\n"
            f"whisper 전사 결과에서 문구를 그대로 복사했는지 확인하거나, "
            f"insert_broll.py --at/--duration으로 타이밍을 수동 지정하라."
        )

    # idx가 속한 단어(그 단어의 offset <= idx < 다음 단어의 offset)를 찾는다.
    match_word = offsets[0][1]
    for offset, w in offsets:
        if offset <= idx:
            match_word = w
        else:
            break
    return match_word["start"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("main_video")
    ap.add_argument("output")
    ap.add_argument("--cue-file", required=True, help="큐시트 JSON (phrase/broll/duration 배열)")
    ap.add_argument("--whisper-json", default=None,
                     help="이미 whisper를 돌린 word-timestamp JSON. 없으면 --model로 직접 전사한다")
    ap.add_argument("--model", default="base")
    args = ap.parse_args()

    main_video = Path(args.main_video)
    cues = json.loads(Path(args.cue_file).read_text(encoding="utf-8"))
    if not cues:
        raise SystemExit("cue-file이 비어 있다")

    if args.whisper_json:
        words = load_whisper_words(Path(args.whisper_json))
    else:
        words = transcribe_words(main_video, args.model)

    resolved = []
    for cue in cues:
        phrase = cue["phrase"]
        start = find_phrase_start(phrase, words)
        resolved.append({
            "phrase": phrase,
            "broll": cue["broll"],
            "at": start,
            "duration": float(cue["duration"]),
        })
        print(f"매칭 성공: {phrase!r} → {start:.2f}s (broll={cue['broll']}, {cue['duration']}s)")

    # 시간순으로 정렬해서 insert_broll.py를 순서대로 체이닝한다 (앞 구간부터 처리해야
    # --at 타임스탬프가 원본 기준 그대로 유효하다 — insert_broll.py는 컷을 안 없애고
    # concat만 하므로 길이가 안 바뀐다).
    resolved.sort(key=lambda r: r["at"])

    current = main_video
    with tempfile.TemporaryDirectory() as td:
        for i, r in enumerate(resolved):
            is_last = i == len(resolved) - 1
            step_out = Path(args.output) if is_last else Path(td) / f"step_{i:02d}.mp4"
            subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "insert_broll.py"),
                 str(current), r["broll"], str(step_out),
                 "--at", f"{r['at']:.3f}", "--duration", f"{r['duration']:.3f}"],
                check=True,
            )
            current = step_out

    print(f"B-roll 큐 {len(resolved)}개 전부 매칭+삽입 완료 → {args.output}")


if __name__ == "__main__":
    main()
