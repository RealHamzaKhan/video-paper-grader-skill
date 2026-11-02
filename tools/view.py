#!/usr/bin/env python3
"""view.py - Stage 3 tool for the video-paper-grader skill.

Purpose: look closer at one moment of the video. Three modes:

1. Single frame at full size:
   python3 view.py VIDEO --t 42.5 --out frame.jpg

2. A crop of that frame (fractions of width/height, each 0 to 1).
   Use this to read small text, for example an identity field on a page:
   python3 view.py VIDEO --t 42.5 --crop 0.05 0.15 0.40 0.20 --scale 2 --out crop.jpg

3. A burst sheet: several frames around one moment, packed in one image.
   Use this when a page change is unclear at the normal sampling rate:
   python3 view.py VIDEO --t 42.5 --burst 2 4 --out burst.jpg
   (means: from 2 seconds before to 2 seconds after, 4 frames per second)

Needs: opencv-python-headless, Pillow.
"""
import argparse, os, sys
import cv2
from PIL import Image, ImageDraw


def grab(cap, fps, t):
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000.0)
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--t", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crop", type=float, nargs=4, metavar=("X", "Y", "W", "H"))
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--burst", type=float, nargs=2, metavar=("HALF_WINDOW_SEC", "FPS"))
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: cannot open video: {args.video}")
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    if args.burst:
        half, bfps = args.burst
        times = []
        t = args.t - half
        while t <= args.t + half + 1e-6:
            times.append(round(t, 2))
            t += 1.0 / bfps
        cells = []
        cw = 512
        for tt in times:
            fr = grab(cap, fps, tt)
            if fr is None:
                continue
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            ch = int(cw * im.height / im.width)
            cells.append((tt, im.resize((cw, ch))))
        if not cells:
            print("ERROR: no frames in burst window")
            return 2
        cols = 4
        rows = (len(cells) + cols - 1) // cols
        ch = cells[0][1].height
        label_h = 30
        sheet = Image.new("RGB", (cols * cw, rows * (ch + label_h)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (tt, im) in enumerate(cells):
            r, c = divmod(i, cols)
            x, y = c * cw, r * (ch + label_h)
            sheet.paste(im, (x, y + label_h))
            d.rectangle([x, y, x + cw, y + label_h], fill="black")
            d.text((x + 8, y + 8), f"t={tt}s", fill="white")
        sheet.save(args.out, quality=88)
        print(f"burst sheet written: {args.out} ({len(cells)} frames, t={times[0]}..{times[-1]})")
        return 0

    frame = grab(cap, fps, args.t)
    if frame is None:
        print(f"ERROR: no frame at t={args.t}s")
        return 2
    if args.crop:
        h, w = frame.shape[:2]
        x, y, cw_, ch_ = args.crop
        x0, y0 = int(x * w), int(y * h)
        x1, y1 = int((x + cw_) * w), int((y + ch_) * h)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)
        if x1 <= x0 or y1 <= y0:
            print("ERROR: crop box is empty")
            return 2
        frame = frame[y0:y1, x0:x1]
    if args.scale != 1.0:
        frame = cv2.resize(frame, None, fx=args.scale, fy=args.scale,
                           interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(args.out, frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"frame written: {args.out} (t={args.t}s, size {frame.shape[1]}x{frame.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
