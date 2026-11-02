#!/usr/bin/env python3
"""package.py - Final tool for the video-paper-grader skill.

Purpose: take the agent's grouping decisions and build the outputs:
one folder + one PDF per student, a manifest, and a plain report.

The agent writes grouping.json. This tool only packages. It never
decides which page belongs to whom, and it never invents an identity.
It refuses to run when the grouping is inconsistent:
- the same time is used by two students
- a listed time has no candidate frame near it
- a student has zero pages

grouping.json format:
{
  "students": [
    {"label": "Student 1", "id": "ID-OR-EMPTY", "name": "NAME-OR-EMPTY",
     "pages": [12.0, 15.0, 19.0],
     "flags": ["anything the teacher should know"]}
  ],
  "unassigned": [{"t": 88.0, "reason": "too blurry to place"}]
}

Usage:
  python3 package.py INDEX_JSON FRAMES_DIR GROUPING_JSON OUTDIR

Output in OUTDIR:
  students/S01_<id-or-label>/page_01_t12_0.jpg ... and student.pdf
  manifest.json
  report.txt

Needs: Pillow only.
"""
import json, os, re, sys
from PIL import Image


def slug(text):
    text = re.sub(r"[^A-Za-z0-9]+", "_", str(text or "")).strip("_")
    return text[:40] or "student"


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    index_path, frames_dir, grouping_path, outdir = sys.argv[1:5]
    with open(index_path) as f:
        frames = json.load(f)["frames"]
    with open(grouping_path) as f:
        grouping = json.load(f)

    times = [fr["t"] for fr in frames]
    by_t = {fr["t"]: fr["file"] for fr in frames}

    def nearest(t, tol=1.0):
        best = min(times, key=lambda x: abs(x - t))
        return best if abs(best - t) <= tol else None

    errors = []
    used = {}
    plan = []
    for si, st in enumerate(grouping.get("students", []), 1):
        pages = sorted(st.get("pages", []))
        if not pages:
            errors.append(f"student {si} ({st.get('label')}): zero pages")
            continue
        resolved = []
        for t in pages:
            nt = nearest(float(t))
            if nt is None:
                errors.append(f"student {si} ({st.get('label')}): no frame near t={t}")
                continue
            if nt in used and used[nt] != si:
                errors.append(f"t={nt} used by both student {used[nt]} and student {si}")
                continue
            # the same time may appear twice for the SAME student only:
            # that is how a two-page spread (open book) is packaged
            used[nt] = si
            resolved.append(nt)
        plan.append((si, st, resolved))
    if errors:
        print("REFUSED: grouping has problems, nothing was written:")
        for e in errors:
            print(" -", e)
        return 2

    os.makedirs(outdir, exist_ok=True)
    manifest = {"students": [], "unassigned": grouping.get("unassigned", [])}
    lines = []
    total_pages = 0
    for si, st, resolved in plan:
        ident = st.get("id") or st.get("name") or st.get("label") or f"student{si}"
        folder = os.path.join(outdir, "students", f"S{si:02d}_{slug(ident)}")
        os.makedirs(folder, exist_ok=True)
        imgs = []
        page_entries = []
        for k, nt in enumerate(resolved, 1):
            src = os.path.join(frames_dir, by_t[nt])
            im = Image.open(src).convert("RGB")
            name = f"page_{k:02d}_t{nt}.jpg"
            im.save(os.path.join(folder, name), quality=90)
            imgs.append(im)
            page_entries.append({"page": k, "t": nt, "file": name})
        pdf_path = os.path.join(folder, "student.pdf")
        imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])
        total_pages += len(resolved)
        manifest["students"].append({
            "n": si, "label": st.get("label", ""), "id": st.get("id", ""),
            "name": st.get("name", ""), "folder": os.path.basename(folder),
            "pages": page_entries, "flags": st.get("flags", [])})
        lines.append(f"S{si:02d}  id={st.get('id') or '-'}  name={st.get('name') or '-'}  "
                     f"pages={len(resolved)}  flags={'; '.join(st.get('flags', [])) or '-'}")

    with open(os.path.join(outdir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    header = [f"students: {len(plan)}", f"total_pages_packaged: {total_pages}",
              f"unassigned_frames: {len(manifest['unassigned'])}", ""]
    with open(os.path.join(outdir, "report.txt"), "w") as f:
        f.write("\n".join(header + lines) + "\n")
    print("\n".join(header + lines))
    print(f"output: {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
