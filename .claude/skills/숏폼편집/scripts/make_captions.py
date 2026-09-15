#!/usr/bin/env python3
"""자막 생성: whisper로 받아쓰고, 스타일 프리셋을 적용한 자막을 영상에 번인한다.

사용법:
  python3 make_captions.py input.mp4 output.mp4 \
      [--style ../presets/default_style.json] [--model base] \
      [--translations translations.json]

--translations: 영문 자막(위)을 쓰려면 세그먼트 순서와 같은 영어 문장 배열을
                 담은 JSON 파일을 넘긴다. 번역은 클로드가 대본을 보고 먼저
                 만들어서 파일로 저장해준다 (이 스크립트는 번역을 하지 않는다).
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def transcribe(video: Path, model: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["whisper", str(video), "--model", model, "--output_format", "json",
             "--output_dir", td, "--language", "Korean"],
            check=True,
        )
        data = json.loads((Path(td) / f"{video.stem}.json").read_text())
    return data["segments"]


def wrap_text(text: str, max_chars: int) -> list[str]:
    """한 줄에 다 안 들어가면 단어 경계에서 쪼갠다 — 글자 크기는 줄이지 않는다."""
    words = text.strip().split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = f"{cur} {w}".strip()
        if len(candidate) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines


def ass_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def build_ass(segments: list[dict], style: dict, translations: list[str] | None) -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: KR,{style['font']},{style['korean_size']},{style['korean_color']},&H00000000&,{style['korean_highlight_bg']},1,{style.get('korean_border_style', 1)},{style.get('korean_outline', 8)},0,2,60,60,{style['korean_margin_v']}
Style: EN,{style['font']},{style['english_size']},{style['english_color']},&H00000000&,&H00000000&,0,1,1,0,8,60,60,{style['english_margin_v']}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for idx, seg in enumerate(segments):
        wrapped = wrap_text(seg["text"], style["max_line_chars"])
        span = (seg["end"] - seg["start"]) / max(len(wrapped), 1)
        for i, line in enumerate(wrapped):
            s = seg["start"] + i * span
            e = s + span
            text = line
            marker = style.get("emphasis_marker")
            if marker and marker in text:
                text = text.replace(marker, "")
                text = f"{{\\fscx{style['emphasis_scale']}\\fscy{style['emphasis_scale']}}}{text}"
            lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},KR,,0,0,0,,{text}")

        if style.get("english_top") and translations and idx < len(translations):
            lines.append(
                f"Dialogue: 0,{ass_time(seg['start'])},{ass_time(seg['end'])},EN,,0,0,0,,{translations[idx]}"
            )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--style", default=str(SKILL_DIR / "presets" / "default_style.json"))
    ap.add_argument("--model", default="base")
    ap.add_argument("--translations", default=None)
    args = ap.parse_args()

    video = Path(args.input).resolve()
    output = Path(args.output).resolve()
    style = json.loads(Path(args.style).read_text())
    translations = json.loads(Path(args.translations).read_text()) if args.translations else None
    segments = transcribe(video, args.model)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        ass_path = td_path / "captions.ass"
        ass_path.write_text(build_ass(segments, style, translations), encoding="utf-8")
        # ffmpeg -vf ass=<path> 값에 절대경로(특히 Windows 드라이브 콜론 C:\)를 넣으면
        # 네이티브 Windows ffmpeg.exe(~/.local/bin/ffmpeg 래퍼)의 avfilter 옵션 파서가
        # 콜론 위치에서 옵션 경계를 잘못 잡는 걸 실측으로 확인했다(이스케이프해도 마찬가지).
        # 그래서 cwd를 임시 디렉터리로 잡고 순수 상대 파일명("captions.ass")만 필터에 넣는다.
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video), "-vf", "ass=captions.ass",
             "-c:a", "copy", str(output)],
            check=True, cwd=str(td_path),
        )
    print(f"자막 입혀서 저장: {args.output}")


if __name__ == "__main__":
    main()
