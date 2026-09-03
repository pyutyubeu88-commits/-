#!/usr/bin/env python3
"""가로 영상을 9:16 세로로 바꾸면서 얼굴을 따라 크롭한다.

**기본적으로 스킵한다.** 정적 인터뷰 촬영본처럼 원본이 이미 9:16에 가까우면
(가로세로비 0.55~0.58 사이) 크롭할 이유가 없다 — ffprobe로 종횡비를 먼저 확인해서
이 범위 안이면 얼굴추적을 아예 돌리지 않고 원본을 그대로 통과시킨다. 얼굴추적 동적
크롭은 가로 촬영본 등 종횡비가 명확히 다를 때만(--force로 강제 가능) 실행된다.

사용법:
  python3 reframe_vertical.py input.mp4 output.mp4
  python3 reframe_vertical.py input.mp4 output.mp4 --force   # 종횡비 상관없이 얼굴추적 크롭 강제

얼굴추적 크롭이 실제로 실행될 때만 opencv-python이 필요하다 (pip install opencv-python).
이미 9:16이라 스킵되는 기본 케이스에서는 opencv가 아예 설치돼 있지 않아도 동작한다
(cv2는 얼굴추적 함수 안에서만 지연 임포트한다).
얼굴이 화면 밖으로 안 나가게, 크롭 중심이 초당 너무 빨리 움직이면 속도를 제한한다.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

SAMPLE_EVERY_SEC = 0.3  # 이 간격으로만 얼굴을 찾는다 (매 프레임 검출은 너무 느리다)
MAX_SHIFT_PER_SEC = 400  # 크롭 중심이 초당 이 픽셀 이상 못 움직이게 막아 흔들림 방지
VERTICAL_RATIO_MIN = 0.55  # 이 범위(가로/세로) 안이면 이미 9:16에 가까운 것으로 보고 스킵
VERTICAL_RATIO_MAX = 0.58  # 9:16 = 0.5625


def probe_wh(video: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    )
    w, h = out.stdout.strip().split(",")
    return int(w), int(h)


def detect_face_centers(video: Path) -> tuple[list[tuple[float, float]], float]:
    import cv2  # 얼굴추적이 실제로 필요할 때만 임포트 — 9:16 스킵 경로는 opencv 없이도 동작해야 한다

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    step = max(1, int(fps * SAMPLE_EVERY_SEC))

    centers: list[tuple[float, float]] = []
    last_x = width / 2
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.1, 5)
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                last_x = x + w / 2
            centers.append((frame_idx / fps, last_x))
        frame_idx += 1
    cap.release()
    return centers, width


def smooth(centers: list[tuple[float, float]]) -> list[tuple[float, float]]:
    smoothed = [centers[0]]
    prev_t, prev_x = centers[0]
    for t, x in centers[1:]:
        max_delta = MAX_SHIFT_PER_SEC * (t - prev_t)
        x = max(prev_x - max_delta, min(prev_x + max_delta, x))
        smoothed.append((t, x))
        prev_t, prev_x = t, x
    return smoothed


def build_sendcmd(centers: list[tuple[float, float]], crop_w: int, src_w: float) -> str:
    lines = []
    for t, cx in centers:
        x = max(0, min(int(src_w) - crop_w, int(cx - crop_w / 2)))
        lines.append(f"{t:.3f} crop@c x {x};")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--force", action="store_true",
                     help="이미 9:16에 가까워도 얼굴추적 크롭을 강제 실행한다")
    args = ap.parse_args()

    video = Path(args.input)
    src_w_px, src_h_px = probe_wh(video)
    ratio = src_w_px / src_h_px
    if not args.force and VERTICAL_RATIO_MIN <= ratio <= VERTICAL_RATIO_MAX:
        subprocess.run(["ffmpeg", "-y", "-i", str(video), "-c", "copy", args.output], check=True)
        print(
            f"이미 세로 비율({ratio:.3f}, {src_w_px}x{src_h_px})이라 얼굴추적 크롭 스킵, "
            f"원본 그대로 통과 → {args.output}"
        )
        return

    centers, src_w = detect_face_centers(video)
    if not centers:
        raise SystemExit("얼굴을 못 찾았습니다 — 원본을 확인하세요")
    centers = smooth(centers)

    src_h = src_h_px  # 이미 probe_wh(ffprobe)로 구해뒀다 — cv2를 또 열 필요 없음
    crop_w = int(src_h * 9 / 16)
    initial_x = max(0, min(int(src_w) - crop_w, int(centers[0][1] - crop_w / 2)))

    with tempfile.TemporaryDirectory() as td:
        sendcmd_path = Path(td) / "crop.cmds"
        sendcmd_path.write_text(build_sendcmd(centers, crop_w, src_w))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video),
             "-vf", (f"sendcmd=f={sendcmd_path},"
                      f"crop@c={crop_w}:{src_h}:{initial_x}:0,scale=1080:1920"),
             "-c:a", "copy", args.output],
            check=True,
        )
    print(f"세로 변환 완료 → {args.output}")


if __name__ == "__main__":
    main()
