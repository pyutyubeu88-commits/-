#!/usr/bin/env python3
"""가로 영상을 9:16 세로로 바꾸면서 얼굴을 따라 크롭한다.

사용법:
  python3 reframe_vertical.py input.mp4 output.mp4

opencv-python이 설치돼 있어야 한다 (pip install opencv-python).
얼굴이 화면 밖으로 안 나가게, 크롭 중심이 초당 너무 빨리 움직이면 속도를 제한한다.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import cv2

SAMPLE_EVERY_SEC = 0.3  # 이 간격으로만 얼굴을 찾는다 (매 프레임 검출은 너무 느리다)
MAX_SHIFT_PER_SEC = 400  # 크롭 중심이 초당 이 픽셀 이상 못 움직이게 막아 흔들림 방지


def detect_face_centers(video: Path) -> tuple[list[tuple[float, float]], float]:
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
    args = ap.parse_args()

    video = Path(args.input)
    centers, src_w = detect_face_centers(video)
    if not centers:
        raise SystemExit("얼굴을 못 찾았습니다 — 원본을 확인하세요")
    centers = smooth(centers)

    cap = cv2.VideoCapture(str(video))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
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
