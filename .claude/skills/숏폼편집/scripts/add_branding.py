#!/usr/bin/env python3
"""고정 상단 질문 배너 + 하단 로고 워터마크를 영상 처음부터 끝까지 입힌다.

레퍼런스(치과 인터뷰형 숏폼) 스타일: 흰 띠 배경 위에 "Q. + 질문 2줄"이
영상 내내 고정으로 떠 있고, 하단 좌측에 로고 **이미지**가 고정 워터마크로 깔린다.
자막(make_captions.py)과는 별개 레이어라, 보통 순서는 컷편집 → 리프레임 → 이 스크립트
→ 자막 → qc_check.py.

로고는 drawtext로 브랜드명을 텍스트 재구성하지 않는다 — 원형 아이콘 등 텍스트로 표현 안 되는
요소가 로고 이미지 안에 있을 수 있으므로 항상 실제 로고 PNG를 overlay 필터로 합성한다.

클라이언트별 값(로고 경로, 강조색, 브랜드명)은 스크립트에 하드코딩하지 않고
`clients/<클라이언트명>/config.json`으로 분리한다. 스키마:
  {"logo_path": "...", "accent_color": "#RRGGBB", "brand_name": "..."}
`logo_path`는 config.json 파일이 있는 디렉터리 기준 상대경로도 허용한다.
이렇게 분리해두면 다른 클라이언트 릴스에 이 스킬을 재사용할 때 스마일뷰 브랜드가
스크립트 코드 밖으로 새어나가지 않는다.

사용법 (클라이언트 config 사용, 권장):
  python3 add_branding.py input.mp4 output.mp4 \
      --question "동양인과 서양인" "치아 구조가 다른가요?" \
      --logo \
      --client-config clients/스마일뷰/config.json \
      --font /path/to/Pretendard-Bold.ttf

사용법 (config 없이 직접 지정):
  python3 add_branding.py input.mp4 output.mp4 \
      --question "..." "..." --logo --logo-path assets/logo_smileview.png \
      --accent-color "#225FEC" --font /path/to/Pretendard-Bold.ttf

한글이 들어가므로 fontfile은 한글을 지원하는 폰트여야 한다.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def write_text(td: Path, name: str, text: str) -> Path:
    p = td / name
    p.write_text(text, encoding="utf-8")
    return p


def stage_for_filter(td_path: Path, src, name: str) -> str:
    """필터 옵션 값(fontfile=/textfile=) 안에 박힐 경로를 td_path 안의 안전한 파일명으로
    바꿔치기한다 — 절대경로/드라이브 콜론/한글·공백 전혀 없는 상대 파일명만 리턴한다.

    `~/.local/bin/ffmpeg`는 네이티브 Windows ffmpeg.exe 래퍼인데, 인자 하나 전체가
    `/mnt/...`·`/home/...`로 시작할 때만 `wslpath -w`로 자동 변환해준다. -filter_complex/-vf
    값은 필터 전체가 한 덩어리 문자열이라 그 안에 박힌 경로는 안 바뀐다. Windows 경로로
    변환해서 콜론을 이스케이프(`C\\:`)해봐도 이 환경에서 avfilter 파서가 옵션 경계를
    잘못 잡는 걸 실측으로 확인했다 — 그래서 아예 경로 자체를 안 쓰는 쪽으로 우회한다:
    파일을 td_path로 복사해두고, ffmpeg 실행 시 cwd를 td_path로 잡아서 필터에는
    순수 상대 파일명만 넣는다."""
    dst = td_path / name
    shutil.copy(str(src), str(dst))
    return name


def to_ffmpeg_color(hex_or_0x: str) -> str:
    """'#225FEC' / '225FEC' / '0x225FEC' 어떤 형태로 와도 ffmpeg drawtext가 먹는
    '0xRRGGBB' 형태로 통일한다."""
    v = hex_or_0x.strip()
    if v.startswith("#"):
        v = "0x" + v[1:]
    elif not v.lower().startswith("0x"):
        v = "0x" + v
    return v


def load_client_config(path: str) -> dict:
    cfg_path = Path(path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if "logo_path" in cfg:
        logo_path = Path(cfg["logo_path"])
        if not logo_path.is_absolute():
            logo_path = (cfg_path.parent / logo_path).resolve()
        cfg["logo_path"] = str(logo_path)
    return cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--question", nargs=2, metavar=("LINE1", "LINE2"),
                     help="상단 고정 질문 배너 2줄 (1줄=검정, 2줄=강조색)")
    ap.add_argument("--logo", action="store_true",
                     help="하단 좌측에 로고 이미지를 워터마크로 합성한다 (텍스트 재구성 아님)")
    ap.add_argument("--logo-path", default=None,
                     help="로고 PNG 경로. --client-config가 있으면 거기서 읽은 값이 기본값")
    ap.add_argument("--accent-color", default=None,
                     help="질문 배너 강조색(hex, 예: #225FEC). 없으면 --client-config → "
                          "--style의 header_accent_color 순으로 사용")
    ap.add_argument("--client-config", default=None,
                     help="clients/<이름>/config.json — logo_path/accent_color/brand_name")
    ap.add_argument("--style", default=str(SKILL_DIR / "presets" / "default_style.json"))
    ap.add_argument("--font", required=True, help="한글 지원 폰트 파일(.ttf/.otf) 경로")
    args = ap.parse_args()

    if not args.question and not args.logo:
        raise SystemExit("--question 또는 --logo 중 하나는 있어야 한다")

    client_cfg = load_client_config(args.client_config) if args.client_config else {}

    style = json.loads(Path(args.style).read_text())["branding"]

    accent_color = to_ffmpeg_color(
        args.accent_color or client_cfg.get("accent_color") or style["header_accent_color"]
    )

    logo_path = args.logo_path or client_cfg.get("logo_path")
    if args.logo and not logo_path:
        raise SystemExit(
            "--logo를 쓰려면 --logo-path 또는 로고 경로가 담긴 --client-config가 필요하다"
        )
    if args.logo and not Path(logo_path).is_file():
        raise SystemExit(f"로고 파일을 찾을 수 없다: {logo_path}")

    # 아래에서 ffmpeg를 td(임시 디렉터리)를 cwd로 잡고 돌릴 것이므로, 상대경로로 받았을 수도
    # 있는 입력/출력/로고 경로는 미리 절대경로로 고정해둔다.
    input_path = str(Path(args.input).resolve())
    output_path = str(Path(args.output).resolve())
    logo_abs = str(Path(logo_path).resolve()) if args.logo else None

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        text_filters = []

        if args.question:
            fontfile = stage_for_filter(td_path, args.font, "font" + Path(args.font).suffix)
            label = stage_for_filter(td_path, write_text(td_path, "_qlabel.txt", "Q."), "qlabel.txt")
            q1 = stage_for_filter(td_path, write_text(td_path, "_q1.txt", args.question[0]), "q1.txt")
            q2 = stage_for_filter(td_path, write_text(td_path, "_q2.txt", args.question[1]), "q2.txt")
            text_filters += [
                f"drawbox=x=0:y=0:w=iw:h={style['header_height']}:color={style['header_bg']}@1:t=fill",
                (f"drawtext=fontfile={fontfile}:textfile={label}:fontcolor={accent_color}"
                 f":fontsize={style['header_label_size']}:x=(w-text_w)/2:y={style['header_label_y']}"),
                (f"drawtext=fontfile={fontfile}:textfile={q1}:fontcolor={style['header_line1_color']}"
                 f":fontsize={style['header_font_size']}:x=(w-text_w)/2:y={style['header_line1_y']}"),
                (f"drawtext=fontfile={fontfile}:textfile={q2}:fontcolor={accent_color}"
                 f":fontsize={style['header_font_size']}:x=(w-text_w)/2:y={style['header_line2_y']}"),
            ]

        if args.logo:
            # 1) 원본 영상에 텍스트 필터(질문 배너)를 먼저 입힌 [base] 스트림을 만들고
            # 2) 로고 PNG를 --logo-width로 스케일한 뒤 [base] 위에 overlay로 합성한다.
            base_chain = ",".join(text_filters) if text_filters else "null"
            logo_w = style["logo_width"]
            logo_x = style["logo_x"]
            margin_b = style["logo_margin_bottom"]
            filter_complex = (
                f"[0:v]{base_chain}[base];"
                f"[1:v]scale={logo_w}:-1[logo];"
                f"[base][logo]overlay=x={logo_x}:y=H-h-{margin_b}"
            )
            cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_abs,
                   "-filter_complex", filter_complex,
                   "-c:a", "copy", output_path]
        else:
            cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", ",".join(text_filters),
                   "-c:a", "copy", output_path]

        subprocess.run(cmd, check=True, cwd=str(td_path))
    print(f"브랜딩(질문 배너/로고) 입혀서 저장: {args.output}")


if __name__ == "__main__":
    main()
