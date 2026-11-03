#!/usr/bin/env python3
"""scanify.py - Optional tool for the video-paper-grader skill (v1.2).

Purpose: make a "scan copy" of a page image: easier to read, closer to
what a document scanner produces. Steps, all conservative:
  1. If a clear page quadrilateral is found, straighten by perspective
     warp. If not found, keep the original geometry. Never force it.
  2. Flatten the lighting (divide by a blurred background estimate):
     removes shadows and glare, evens the paper brightness.
  3. CLAHE contrast on the flattened grey image.
  4. Mild sharpening (unsharp mask).

It NEVER edits an original. Output is always a NEW file/folder.
Default output is the enhanced grey version. With --binary it also
writes a hard black-and-white variant (<name>_bw.jpg): an extra view
only. Hard B/W can erase faint pencil; never package from it without
comparing against the original on the faintest page (see SKILL.md).

Modes:
  Single image:
    python3 scanify.py IN.jpg OUT.jpg [--binary]
  Packaged job: enhance every packaged page of a finished job and
  build a scan PDF per student (originals stay untouched):
    python3 scanify.py --packaged JOB/out
    -> writes JOB/out/students/<S>/scan/page_XX.jpg and student_scan.pdf

Needs: opencv-python-headless, numpy, Pillow (PDF building).
"""
import argparse, glob, os, sys
import cv2
import numpy as np


def find_quad(gray):
    """Largest 4-point contour covering a sane part of the image, or None."""
    h, w = gray.shape
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_area = h * w
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        area = cv2.contourArea(cnt)
        if area < 0.35 * img_area:
            break
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype(np.float32)
    return None


def order_points(pts):
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # top-left
    rect[2] = pts[np.argmax(s)]       # bottom-right
    d = np.diff(pts, axis=1).ravel()
    rect[1] = pts[np.argmin(d)]       # top-right
    rect[3] = pts[np.argmax(d)]       # bottom-left
    return rect


def warp(img, quad):
    rect = order_points(quad)
    (tl, tr, br, bl) = rect
    width = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    height = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    if width < 200 or height < 200:
        return None
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1],
                    [0, height - 1]], dtype=np.float32)
    m = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, m, (width, height))


def enhance(img):
    """Lighting flatten + CLAHE + mild sharpen. Returns grey-as-BGR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # background estimate: large median blur; divide removes slow light changes
    bg = cv2.medianBlur(gray, 51)
    flat = cv2.divide(gray, bg, scale=255)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    out = clahe.apply(flat)
    blur = cv2.GaussianBlur(out, (0, 0), 2.0)
    out = cv2.addWeighted(out, 1.4, blur, -0.4, 0)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def binary_version(enhanced_bgr):
    gray = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 12)
    return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)


def scanify_file(inp, outp, binary=False, warp_first=False):
    img = cv2.imread(inp)
    if img is None:
        print(f"ERROR: cannot read {inp}")
        return False
    # Warp is OPT-IN (--warp): auto-straighten can find the wrong quad on
    # messy frames and skew the page (seen in testing). Default = light
    # and contrast only, geometry untouched.
    warped = False
    if warp_first:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        quad = find_quad(gray)
        if quad is not None:
            w = warp(img, quad)
            if w is not None:
                img = w
                warped = True
    out = enhance(img)
    os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
    cv2.imwrite(outp, out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    msg = f"{os.path.basename(inp)} -> {os.path.basename(outp)} (warped: {'yes' if warped else 'no'}, size {out.shape[1]}x{out.shape[0]})"
    if binary:
        bw_path = outp.rsplit('.', 1)[0] + '_bw.jpg'
        cv2.imwrite(bw_path, binary_version(out), [cv2.IMWRITE_JPEG_QUALITY, 92])
        msg += f" + {os.path.basename(bw_path)}"
    print(msg)
    return True


def packaged_mode(outdir):
    from PIL import Image
    students = sorted(glob.glob(os.path.join(outdir, "students", "*")))
    if not students:
        print(f"ERROR: no students under {outdir}/students")
        return 2
    total = 0
    for sdir in students:
        pages = sorted(glob.glob(os.path.join(sdir, "page_*.jpg")))
        if not pages:
            continue
        scan_dir = os.path.join(sdir, "scan")
        os.makedirs(scan_dir, exist_ok=True)
        imgs = []
        for p in pages:
            outp = os.path.join(scan_dir, os.path.basename(p))
            if scanify_file(p, outp):
                imgs.append(Image.open(outp).convert("RGB"))
                total += 1
        if imgs:
            pdf = os.path.join(sdir, "student_scan.pdf")
            imgs[0].save(pdf, save_all=True, append_images=imgs[1:])
            print(f"{os.path.basename(sdir)}: scan PDF with {len(imgs)} pages -> {pdf}")
    print(f"scanified_pages: {total}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--binary", action="store_true")
    ap.add_argument("--warp", action="store_true",
                    help="also try perspective straighten (default OFF: risky on messy frames)")
    ap.add_argument("--packaged", metavar="OUTDIR")
    args = ap.parse_args()
    if args.packaged:
        return packaged_mode(args.packaged)
    if not args.input or not args.output:
        print(__doc__)
        return 2
    return 0 if scanify_file(args.input, args.output, args.binary, args.warp) else 2


if __name__ == "__main__":
    sys.exit(main())
