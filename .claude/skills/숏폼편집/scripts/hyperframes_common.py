#!/usr/bin/env python3
"""HyperFrames 모션그래픽 스크립트들이 같이 쓰는 헬퍼.

HyperFrames(heygen-com/hyperframes, Apache 2.0)는 HTML을 헤드리스 크롬으로
프레임 단위 렌더링해서 ffmpeg로 인코딩하는 오픈소스 렌더러다. API 키도 계정도
필요 없고 전부 로컬에서 돈다 — 이 스킬의 "전부 무료 로컬" 원칙을 깨지 않는다.

여기서 하는 일은 딱 두 가지:
  1) templates/*.html 을 실제 값으로 채워서 임시 HyperFrames 프로젝트를 만들고
     `--format mov`(ProRes 4444, yuva444p10le)로 **알파 채널 있는** 클립을 렌더한다
  2) 그 클립을 ffmpeg overlay로 원본 영상 위에 얹는다 (원본 길이·음성 그대로)

이 파일은 직접 실행하지 않는다. hyperframes_branding.py / hyperframes_emphasis.py /
hyperframes_graphic.py 가 import 해서 쓴다.

템플릿은 GSAP 같은 외부 CDN 스크립트를 안 쓰고 순수 CSS @keyframes만 쓴다.
HyperFrames 런타임에 CSS/WAAPI 어댑터가 있어서 document.getAnimations()를
프레임 시각마다 seek 해준다 (실측 확인함). 그래서 인터넷 없이도 렌더된다.
대신 GSAP 타임라인을 등록하지 않으므로 템플릿 루트에는 반드시 `data-no-timeline`이
있어야 한다 — 없으면 렌더마다 45초를 그냥 기다린다.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"
DEFAULT_STYLE = SKILL_DIR / "presets" / "default_style.json"

# 실제로 확인한 버전으로 고정한다. 다른 버전을 쓰고 싶으면
# HYPERFRAMES_CMD="npx --yes hyperframes@latest" 처럼 환경변수로 덮어쓴다.
PINNED_VERSION = "0.8.26"


# ---------------------------------------------------------------- 환경 점검

def hyperframes_argv() -> list[str]:
    """HyperFrames CLI 실행 명령. HYPERFRAMES_CMD 환경변수로 덮어쓸 수 있다."""
    override = os.environ.get("HYPERFRAMES_CMD")
    if override:
        return shlex.split(override)
    return ["npx", "--yes", f"hyperframes@{PINNED_VERSION}"]


def require_node() -> None:
    """Node.js 22+ 가 없으면 정적 버전으로 안내하고 멈춘다."""
    if os.environ.get("HYPERFRAMES_CMD"):
        return
    node = shutil.which("node")
    if not node:
        raise SystemExit(
            "Node.js가 없다. HyperFrames 모션 버전은 Node.js 22+ 가 필요하다.\n"
            "  설치: https://nodejs.org (LTS 22 이상)\n"
            "  Node 없이 쓰려면 정적 버전인 add_branding.py를 쓰면 된다."
        )
    out = subprocess.run([node, "--version"], capture_output=True, text=True, check=True)
    major = int(re.sub(r"[^0-9].*$", "", out.stdout.strip().lstrip("v")) or 0)
    if major < 22:
        raise SystemExit(f"Node.js {out.stdout.strip()} — HyperFrames는 22 이상이 필요하다.")


# ---------------------------------------------------------------- 영상 정보
# ffprobe가 없는 환경(정적 ffmpeg 바이너리만 있는 경우)을 위해
# `ffmpeg -i`의 stderr를 파싱하는 폴백을 둔다.

def _ffmpeg_stderr(video: Path) -> str:
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(video)],
        capture_output=True, text=True,
    ).stderr


def probe_duration(video: Path) -> float:
    if shutil.which("ffprobe"):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip())
    m = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)", _ffmpeg_stderr(video))
    if not m:
        raise SystemExit(f"길이를 못 읽었다: {video}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def probe_wh(video: Path) -> tuple[int, int]:
    if shutil.which("ffprobe"):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
            capture_output=True, text=True, check=True,
        )
        w, h = out.stdout.strip().split(",")
        return int(w), int(h)
    m = re.search(r"Video:.*?[,\s](\d{2,5})x(\d{2,5})", _ffmpeg_stderr(video))
    if not m:
        raise SystemExit(f"해상도를 못 읽었다: {video}")
    return int(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------- 스타일

def load_style(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def css_px(value, extent: int) -> str:
    """ffmpeg drawtext의 좌표 표기를 CSS px 값으로 옮긴다.

    add_branding.py는 좌표를 숫자 또는 "h-140"(=아래에서 140px) / "w-60" 으로 쓴다.
    정적 버전과 모션 버전의 위치가 어긋나지 않게 같은 값을 그대로 해석한다.
    extent에는 해당 축의 크기(y면 height, x면 width)를 넘긴다.
    """
    if isinstance(value, (int, float)):
        return f"{value:g}px"
    text = str(value).replace(" ", "")
    m = re.fullmatch(r"[hw]-(\d+(?:\.\d+)?)", text)
    if m:
        return f"{extent - float(m.group(1)):g}px"
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return f"{float(text):g}px"
    raise SystemExit(f"좌표를 CSS로 못 바꾼다: {value!r} (숫자 또는 'h-숫자'/'w-숫자'만 지원)")


def css_color(value: str) -> str:
    """ffmpeg 색 표기를 CSS 색으로 옮긴다.

    default_style.json의 branding은 ffmpeg drawtext 문법을 쓴다:
    "0x2D6CDF"(=CSS #2D6CDF), "white"/"black"(CSS도 같음), "0xRRGGBB@0.5"(알파).
    이걸 그대로 CSS에 넣으면 색이 무시돼서 전부 검정으로 나온다 — 반드시 변환한다.
    """
    text = str(value).strip()
    body, _, alpha = text.partition("@")
    if body.lower().startswith("0x"):
        body = "#" + body[2:]
    if alpha:
        m = re.fullmatch(r"#([0-9a-fA-F]{6})", body)
        if m:
            r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
            return f"rgba({r},{g},{b},{float(alpha)})"
    return body


# ---------------------------------------------------------------- 렌더

def render_alpha_clip(
    template: str,
    props: dict,
    out_mov: Path,
    width: int,
    height: int,
    duration: float,
    font: Path,
    fps: int = 30,
    keep_project: Path | None = None,
    quality: str = "high",
) -> Path:
    """템플릿 + props → 알파 채널 있는 ProRes 4444 .mov 를 렌더한다."""
    require_node()
    src = TEMPLATE_DIR / template
    if not src.exists():
        raise SystemExit(f"템플릿이 없다: {src}")
    font = Path(font).resolve()
    if not font.exists():
        raise SystemExit(f"폰트 파일이 없다: {font}")

    out_mov = out_mov.resolve()
    out_mov.parent.mkdir(parents=True, exist_ok=True)
    project = Path(keep_project).resolve() if keep_project else out_mov.parent / f".hf_{out_mov.stem}"
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)

    # 폰트는 프로젝트 안에 복사해서 상대 경로로 참조한다.
    # (렌더 중 페이지는 localhost로 서빙되므로 file:// 폰트는 막힌다)
    font_file = f"font{font.suffix.lower()}"
    shutil.copy(font, project / font_file)

    # </script> 가 JSON 안에 들어가면 스크립트 태그가 조기 종료되므로 막는다
    props_json = json.dumps(props, ensure_ascii=False).replace("</", "<\\/")
    html = src.read_text(encoding="utf-8")
    for key, value in {
        "__W__": str(width),
        "__H__": str(height),
        "__DUR__": f"{duration:.3f}",
        "__FONT_FILE__": font_file,
        "__PROPS_JSON__": props_json,
    }.items():
        html = html.replace(key, value)
    (project / "index.html").write_text(html, encoding="utf-8")

    cmd = [*hyperframes_argv(), "render", str(project),
           "--format", "mov", "--fps", str(fps), "--quality", quality,
           "-o", str(out_mov), "--quiet"]
    print(f"[hyperframes] {duration:.2f}s / {width}x{height} / {fps}fps 렌더 중…", file=sys.stderr)
    subprocess.run(cmd, check=True)
    if not out_mov.exists():
        raise SystemExit(f"렌더는 끝났는데 파일이 없다: {out_mov}")

    if keep_project:
        print(f"[hyperframes] 프로젝트 남김: {project}\n"
              f"  미리보기: 그 폴더에서 npx hyperframes@{PINNED_VERSION} preview", file=sys.stderr)
    else:
        shutil.rmtree(project, ignore_errors=True)
    return out_mov


# ---------------------------------------------------------------- 합성

def composite_hold(base: Path, clip: Path, output: Path, width: int, height: int,
                   base_duration: float) -> None:
    """짧게 렌더한 클립을 얹고, 마지막 프레임을 영상 끝까지 그대로 붙잡아 둔다.

    배너/로고는 등장 애니메이션이 끝나면 그대로 고정이라, 40초짜리를 통째로
    렌더할 필요가 없다. 2초만 렌더하고 tpad=stop_mode=clone으로 늘린다.
    (렌더 시간이 20배 가까이 줄어든다)
    """
    pad = max(base_duration + 1.0, 1.0)
    filter_complex = (
        f"[1:v]format=rgba,scale={width}:{height},"
        f"tpad=stop_mode=clone:stop_duration={pad:.3f}[ov];"
        f"[0:v][ov]overlay=0:0:format=auto:shortest=1[vout]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(base), "-i", str(clip),
         "-filter_complex", filter_complex,
         "-map", "[vout]", "-map", "0:a?",
         "-c:a", "copy", str(output)],
        check=True,
    )


def composite_timed(base: Path, clips: list[tuple[Path, float, float]], output: Path,
                    width: int, height: int) -> None:
    """[(클립, 시작초, 길이초), ...] 를 각자 구간에만 얹는다.

    setpts로 클립을 시작 시각까지 밀고, enable=between(t,...)로 그 구간에만 켠다.
    원본 길이도 음성도 안 바뀐다.
    """
    parts: list[str] = []
    inputs: list[str] = []
    cur = "[0:v]"
    for i, (clip, start, dur) in enumerate(clips):
        inputs += ["-i", str(clip)]
        idx = i + 1
        end = start + dur
        parts.append(
            f"[{idx}:v]format=rgba,scale={width}:{height},setpts=PTS+{start:.3f}/TB[ov{idx}]"
        )
        nxt = "[vout]" if i == len(clips) - 1 else f"[b{idx}]"
        parts.append(
            f"{cur}[ov{idx}]overlay=0:0:format=auto:eof_action=pass:"
            f"enable='between(t,{start:.3f},{end:.3f})'{nxt}"
        )
        cur = nxt

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(base), *inputs,
         "-filter_complex", ";".join(parts),
         "-map", "[vout]", "-map", "0:a?",
         "-c:a", "copy", str(output)],
        check=True,
    )
