#!/usr/bin/env python3
"""sheets.py - Stage 2 tool for the video-paper-grader skill.

Purpose: pack candidate frames into labelled contact sheets, so the agent
can judge the structure of a whole video by looking at a few images
instead of hundreds of single frames.

Every cell shows its time label (for example "t=42.5s") burned into the
image. Cells are in time order: left to right, then top to bottom.

Usage:
  python3 sheets.py INDEX_JSON FRAMES_DIR OUTDIR [--per-sheet 25] [--cols 5] [--cell-w 512]

Output in OUTDIR:
  sheet_001.jpg, sheet_002.jpg, ...
  sheets_index.json  (which times are on which sheet)

Needs: opencv-python-headless (or Pillow only - this file uses Pillow), numpy not needed.
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("frames_dir")
    ap.add_argument("outdir")
    ap.add_argument("--per-sheet", type=int, default=25)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--cell-w", type=int, default=512)
    args = ap.parse_args()

    with open(args.index) as f:
        index = json.load(f)
    frames = index["frames"]
    if not frames:
        print("ERROR: index has no frames")
        return 2
    os.makedirs(args.outdir, exist_ok=True)

    label_h = 30
    sheets_meta = []
    n_sheets = math.ceil(len(frames) / args.per_sheet)
    for s in range(n_sheets):
        chunk = frames[s * args.per_sheet:(s + 1) * args.per_sheet]
        rows = math.ceil(len(chunk) / args.cols)
        # cell height from the first frame's aspect (frames in one video share aspect)
        first = Image.open(os.path.join(args.frames_dir, chunk[0]["file"]))
        cw = args.cell_w
        ch = int(cw * first.height / first.width)
        sheet = Image.new("RGB", (args.cols * cw, rows * (ch + label_h)), "white")
        d = ImageDraw.Draw(sheet)
        for i, fr in enumerate(chunk):
            r, c = divmod(i, args.cols)
            x, y = c * cw, r * (ch + label_h)
            im = Image.open(os.path.join(args.frames_dir, fr["file"])).convert("RGB")
            im = im.resize((cw, ch))
            sheet.paste(im, (x, y + label_h))
            d.rectangle([x, y, x + cw, y + label_h], fill="black")
            tag = "C " if fr["kind"] == "change" else ""
            d.text((x + 8, y + 8), f"{tag}t={fr['t']}s", fill="white")
        name = f"sheet_{s + 1:03d}.jpg"
        sheet.save(os.path.join(args.outdir, name), quality=88)
        sheets_meta.append({"sheet": name, "times": [fr["t"] for fr in chunk]})
        print(f"{name}: times {chunk[0]['t']} .. {chunk[-1]['t']} ({len(chunk)} frames)")

    with open(os.path.join(args.outdir, "sheets_index.json"), "w") as f:
        json.dump({"sheets": sheets_meta}, f, indent=1)
    print(f"sheets_written: {n_sheets}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
