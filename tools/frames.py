#!/usr/bin/env python3
"""frames.py - Stage 1 tool for the video-paper-grader skill.

Purpose: turn a video of ANY length into a small set of candidate frames.
- One best (sharpest) frame per time bucket (default: 1 bucket = 1 second).
- Extra frames around moments where the picture changes a lot
  ("change frames"), so a page shown for less than one bucket is not lost.

This tool makes NO decisions about pages or students. It only proposes
candidate frames. The agent judges them later.

Usage:
  python3 frames.py VIDEO OUTDIR [--step 1.0] [--pool-fps 4] [--change-diff 0.08]

Output in OUTDIR:
  frames/f_00042_50.jpg   (file name encodes the time in seconds)
  index.json              (video info + one entry per chosen frame)

Needs: opencv-python-headless, numpy. No internet, no API keys.
"""
import argparse, json, os, sys
import cv2
import numpy as np


def sharpness(gray_small):
    return float(cv2.Laplacian(gray_small, cv2.CV_64F).var())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("outdir")
    ap.add_argument("--step", type=float, default=1.0, help="bucket size in seconds")
    ap.add_argument("--pool-fps", type=float, default=4.0, help="how often to sample the video")
    ap.add_argument("--change-diff", type=float, default=0.08,
                    help="mean abs difference (0-1) on tiny thumbnails that counts as a big change")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        print(f"ERROR: video not found: {args.video}")
        return 2
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: cannot open video: {args.video}")
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total else 0.0

    frames_dir = os.path.join(args.outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    pool_every = max(1, int(round(fps / args.pool_fps)))
    buckets = {}          # bucket_id -> (sharpness, frame_index)
    pool = []             # (t, frame_index, sharpness, thumb64) for change detection
    prev_thumb = None
    boundaries = []       # times where the picture changed a lot

    idx = -1
    while True:
        ok = cap.grab()
        if not ok:
            break
        idx += 1
        if idx % pool_every != 0:
            continue
        ok, frame = cap.retrieve()
        if not ok or frame is None:
            continue
        t = idx / fps
        small = cv2.resize(frame, (640, int(640 * frame.shape[0] / max(1, frame.shape[1]))))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        sh = sharpness(gray)
        thumb = cv2.resize(gray, (64, 64)).astype(np.float32) / 255.0
        if prev_thumb is not None:
            d = float(np.mean(np.abs(thumb - prev_thumb)))
            if d >= args.change_diff:
                boundaries.append(t)
        prev_thumb = thumb
        pool.append((t, idx, sh))
        b = int(t // args.step)
        if b not in buckets or sh > buckets[b][0]:
            buckets[b] = (sh, idx, t)

    chosen = {}  # frame_index -> (t, kind, sharpness)
    for b, (sh, fi, t) in buckets.items():
        chosen[fi] = (t, "bucket", sh)
    # change frames: sharpest pool frame within +-0.5s of each boundary,
    # if that frame is not already chosen
    for bt in boundaries:
        near = [(sh, fi, t) for (t, fi, sh) in pool if abs(t - bt) <= 0.5]
        if not near:
            continue
        sh, fi, t = max(near)
        if fi not in chosen:
            chosen[fi] = (t, "change", sh)

    entries = []
    for fi in sorted(chosen, key=lambda k: chosen[k][0]):
        t, kind, sh = chosen[fi]
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok or frame is None:
            print(f"WARNING: could not re-read frame at t={t:.2f}s, skipped")
            continue
        whole = int(t)
        frac = min(99, int(round((t - whole) * 100)))
        name = f"f_{whole:05d}_{frac:02d}.jpg"
        path = os.path.join(frames_dir, name)
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        entries.append({"file": name, "t": round(t, 2), "kind": kind, "sharpness": round(sh, 1)})
    cap.release()

    index = {"video": os.path.abspath(args.video), "fps": round(fps, 3),
             "duration_sec": round(duration, 2), "step_sec": args.step,
             "frames": entries}
    with open(os.path.join(args.outdir, "index.json"), "w") as f:
        json.dump(index, f, indent=1)

    print(f"video: {args.video}")
    print(f"duration_sec: {duration:.1f}")
    print(f"buckets: {len(buckets)}")
    print(f"change_boundaries: {len(boundaries)}")
    print(f"frames_written: {len(entries)}")
    print(f"index: {os.path.join(args.outdir, 'index.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
