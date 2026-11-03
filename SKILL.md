---
name: video-paper-grader
description: Turn ONE long video of paper work (a teacher flipping through many students' papers, booklets, notebooks or sheets) into one clean PDF per student. Works for any video length, any paper type, any layout, any language. The agent is the judge; the scripts are only hands.
---

# Video Paper Grader (agent skill)

## What this skill does

Input: one video file. A person filmed paper work page by page, for
example a teacher flipping through a whole class's exam booklets.

Output: one folder and one PDF per student, in the right order, plus a
manifest and a plain report. Grading the work is a separate step and is
NOT part of this skill. Never invent marks. Never invent identities.

## The one big rule

**You are the judge. The scripts are only your hands.**

Scripts extract frames and build files. They never decide anything.
Every decision (what is a page, whose page it is, what the identity
says) is made by you, by looking, and is checked by you before the run
ends. If a script output looks wrong, the script output is wrong, not
your eyes. Find the cause, fix it, run again.

## Hard rules (never break these)

1. **Fully generic.** Never assume anything about this video from any
   other video: not the school, not the exam, not the paper layout, not
   where identity is written, not how many pages a student has, not the
   language, not the filming style. Everything you need must come from
   THIS video, by looking at it.
2. **Never enforce a fix for one situation.** If something fails, fix
   the general cause. If you learn a lesson, write it in general words
   (see Phase 7). A lesson that names one school, one exam or one paper
   type is a bad lesson.
3. **Never guess an identity.** If you cannot read it after all zoom
   steps, label the student by order ("Student 3") and flag it.
   A wrong identity is much worse than a missing one.
3b. **A new student needs identity evidence.** A student may only be
   started by (a) a page carrying identity that differs from the
   open student, or (b) a witnessed event: the previous work is taken
   away and a new stack or booklet is placed. A page with NO identity
   and NO such event NEVER starts a student, even if its content,
   subject or handwriting looks different, and even if it is the last
   page of the video. The end of a video is not evidence. Such a page
   joins the currently open student with a flag, or goes to
   unassigned with a written reason. Inventing a student is the worst
   error this skill can make.
4. **Never drop a frame silently.** Every candidate frame ends in
   exactly one place: packaged, an extra view of a packaged page,
   empty, or unassigned with a written reason.
5. **Write everything down.** Do not keep numbers or decisions in your
   head. The state file and the notes file are your memory. If it is
   not written, it did not happen.
6. **Small steps.** One phase at a time. One sheet at a time. Finish
   each sheet's notes before opening the next sheet.

## What you need

- The video file path.
- Optional, only if the teacher gave them: expected student count,
  a class roster, course or exam name. All optional. The skill works
  without them.
- Python 3 with: opencv-python-headless, numpy, Pillow.
- The tools in this skill's `tools/` folder: `frames.py`, `sheets.py`,
  `view.py`, `package.py`.
- Templates in `templates/`: `state.md`, `sheet_notes.md`,
  `grouping.json`.

## Job folder layout (create exactly this)

```
JOB/
  state.md          (copy of templates/state.md, kept updated)
  sheet_notes.md    (copy of templates/sheet_notes.md, kept updated)
  index.json        (made by frames.py)
  frames/           (made by frames.py)
  sheets/           (made by sheets.py)
  views/            (full-size frames and crops you make with view.py)
  grouping.json     (you write this in Phase 5)
  out/              (made by package.py: students/, manifest.json, report.txt)
```

Below, `SKILL` means this skill's folder and `JOB` the job folder.
Run all commands from the `SKILL` folder unless told otherwise.

---

## Phase 0 - Understand the video BEFORE any processing

Do not skip this phase. A run that starts blind ends wrong.

1. Create the JOB folder. Copy `templates/state.md` to `JOB/state.md`
   and `templates/sheet_notes.md` to `JOB/sheet_notes.md`.
2. Fill the "Job" section of state.md with what the teacher told you.
   Write "not told" where you were not told. Do not fill gaps yourself.
3. Take three sample frames with the view tool (start, middle, end).
   You need the duration first: run frames.py now (Phase 1, step 1-2)
   to learn it, then come back here. Commands:
   - `python3 tools/view.py VIDEO --t 2 --out JOB/views/sample_start.jpg`
   - `python3 tools/view.py VIDEO --t MIDDLE --out JOB/views/sample_mid.jpg`
   - `python3 tools/view.py VIDEO --t END_MINUS_2 --out JOB/views/sample_end.jpg`
4. LOOK at the three samples. Then fill the "What this video is"
   section of state.md, in your own words:
   - What paper is this (booklet, loose sheets, notebooks, other)?
   - What does the start of one student's work look like in THIS video?
   - Is identity written anywhere? Where on the page does it seem to be?
   - How is it filmed (tripod, hand held, moving, still)?
   - What problems can you already see (shadows, two pages at once,
     fast flipping, dark parts, hands covering pages)?
5. Read `LESSONS.md` in this skill folder, fully. Old runs paid for
   those lessons. Apply any that fit what you just saw.

CHECKPOINT 0: state.md "What this video is" is filled from looking,
not from guessing. If all three samples show no paper at all, stop:
tell the teacher the video seems wrong (this is Blocker B4).

## Phase 1 - Extract candidate frames

1. Run: `python3 tools/frames.py VIDEO JOB`
   It prints duration, buckets, change boundaries, frames written.
2. Write those four numbers into state.md.
3. Sanity check (do the arithmetic, write it):
   - Expected frames is about: duration in seconds (one per second)
     plus some change frames. If frames written is less than half the
     duration, something is wrong. Go to the Failure Table.
   - If frames written is 0: stop, Failure Table.
4. If the teacher will film future videos, nothing to change here.
   This tool is deliberately generous: extra frames are fine, you will
   sort them. Missing frames are the real danger, and the change
   frames exist to prevent that.

CHECKPOINT 1: index.json exists and its frame count passed the sanity
check above.

## Phase 2 - Build contact sheets

1. Run: `python3 tools/sheets.py JOB/index.json JOB/frames JOB/sheets`
2. Write the number of sheets into state.md.
3. Open sheet_001.jpg and look: every cell must show a time label like
   `t=42.5s` (a `C` before the time means a change frame). If labels
   are missing or cells are black, go to the Failure Table.

CHECKPOINT 2: sheets exist, labels readable.

## Phase 3 - Judge the sheets (the core work)

Work in batches. One batch = at most 10 sheets. After every sheet,
update state.md (students so far, who is currently open, last time
processed, unclear list). If you stop and resume later, state.md tells
you exactly where you were. Never re-judge a finished sheet unless
Phase 6 verification fails.

For EACH sheet, in order:

1. Open the sheet image. Look at the whole sheet first: get the feel
   of this part of the video (same student continuing? new stacks?).
2. Then go cell by cell, in time order, and fill one row per cell in
   sheet_notes.md. Every cell gets a row. Use exactly these codes:

   | Code | Meaning | Use it when |
   |------|---------|-------------|
   | FIRST | This frame starts a NEW student's work | See evidence rules below |
   | SAME | Same page as the previous frame | Content is the same page; only the camera moved, or the page was shown longer |
   | DUP | Same page as an EARLIER page of the current student, shown again | The person flipped back, or re-showed a page. Content matches an earlier page exactly. Counts as an extra view, not a new page |
   | NEW | A new page of the CURRENT student | Page turned; work continues (text continues, next question, page number goes up by one) |
   | TWO | Two pages visible in one frame | Open book or two sheets side by side; counts as 2 pages |
   | EMPTY | No usable page | Desk, hand only, motion blur, a flip in mid-air |
   | UNCLEAR | You cannot tell yet | You will resolve it in Phase 4. Never leave it forever |

3. Evidence rules for FIRST (a new student). Mark FIRST only when you
   have ONE strong sign or TWO weak signs. Write the sign in the
   Evidence column.
   - Strong signs: a page carrying identity fields (name, roll, ID,
     signature area) with writing in them; work clearly restarting
     (first question again, page numbered 1, a fresh title page);
     a new booklet or stack being placed after the old one was taken
     away.
   - Weak signs: handwriting style clearly changes; paper or page
     design changes; a blank or cover-like page appears between work.
   - NOT a sign by itself: a page that merely looks different, a new
     question starting, a page turned faster than others, a different
     subject or topic than the previous pages, or the video ending.
     (See Hard Rule 3b: without identity or a witnessed new-stack
     event, it is never a new student.)
   Why so strict: a false FIRST splits one student into two. A missed
   FIRST merges two students into one. Both are bad. When torn between
   FIRST and NEW, mark UNCLEAR and let Phase 4 decide with full-size
   frames.
4. Same student, new booklet: a FIRST-looking page whose identity
   matches the current student, or an earlier student, is NOT a new
   student. One student can have several booklets, folders or bundles
   in one video. Mark it FIRST-BOOKLET in the notes, keep that same
   student open, and add the flag "multiple booklets" for the report.
   Identity decides, never the cover.
5. Identity note: when you mark FIRST, also write in the Evidence
   column anything you can already read of the identity, even partly.
   You will read it properly in Phase 4.
6. After the sheet's rows, answer the three lines at the bottom of the
   sheet block (new students, page count, unclear list). Page count
   rule: FIRST = 1 page, NEW = 1 page, TWO = 2 pages, SAME = 0,
   DUP = 0, EMPTY = 0, UNCLEAR = wait.
7. Keep a "Distinct pages seen" list in sheet_notes.md, per student:
   every different page you have seen, in order, INCLUDING a page you
   only ever saw as one side of a spread. Give each a short name
   (its first words, its diagram, its printed page number if it has
   one). This list, not the frame count, is what packaging must
   match in Phase 6. Pages get lost inside spreads more than
   anywhere else; this list is the net that catches them.
8. Printed page numbers: when pages carry them ("Page No 02" and
   similar), write the number in the Evidence column. Use them in
   Phase 4 to confirm page ORDER, and treat a jump in numbers as a
   warning of a possibly missed page: check that stretch with a
   burst (Phase 4b) before moving on.

CHECKPOINT 3 (per batch): state.md students table matches your notes;
the "currently open" student is the one from the last FIRST; unclear
list is copied into state.md.

## Phase 4 - Zoom: identities, unclear frames, seams

Do these three jobs. Use view.py. Save everything into JOB/views/.

### 4a. Read every identity

For each FIRST frame (list them from your notes), in order:

1. Full frame: `python3 tools/view.py VIDEO --t T --out JOB/views/first_T.jpg`
   Look at it. Find where identity is written ON THIS VIDEO'S pages
   (you noted a guess in Phase 0; now confirm or correct it).
2. If identity text is too small: crop that area and enlarge.
   Crop numbers are fractions of the frame (x, y, width, height,
   each 0 to 1). Example, if identity sits in the top-left quarter:
   `python3 tools/view.py VIDEO --t T --crop 0.0 0.0 0.5 0.25 --scale 2 --out JOB/views/id_T.jpg`
   Look again. If still too small, crop tighter around the exact
   field and use `--scale 3`.
3. Write the identity into state.md EXACTLY as written on the page
   (copy characters, do not "fix" them). Note which parts are an ID
   and which are a name, as they appear.
4. Remember the crop fractions that worked and write them in state.md.
   Reuse them for later FIRST frames of this same video. If a later
   page has its identity somewhere else, find it again by looking at
   the full frame first. The full frame always comes before the crop.
5. If you read the same field twice and get two different readings,
   trust the clearer crop. If both are clear and they still differ,
   write both in state.md and flag that student "identity uncertain".
6. If identity cannot be read after step 2 twice: label the student
   "Student N" (its order number), flag "identity not readable".
   This is allowed. Guessing is not. (If the teacher later must know,
   it becomes Blocker B1 only when the teacher says identity is
   required for every student.)

### 4b. Resolve every UNCLEAR frame

For each UNCLEAR time, in order:

1. Full frame with view.py. Look. Most unclear frames resolve here:
   the sheet cell was just small.
2. If still unclear, burst around the moment:
   `python3 tools/view.py VIDEO --t T --burst 2 4 --out JOB/views/burst_T.jpg`
   This shows 2 seconds before to 2 seconds after, 4 frames a second.
   Decide from the motion: was a page turned? whose page is it?
3. Write the final code into sheet_notes.md (replace UNCLEAR) and
   update the page count line for that sheet.
4. If STILL undecided after the burst: the frame goes to "unassigned"
   in the grouping with the reason "could not place even after burst".
   This is a valid outcome, not a failure.

### 4c. Check the seams

For every student: look at full-size frames of their FIRST page and
their LAST page (use view.py). Ask: does the last page belong with the
first (same handwriting family, same paper, work continues naturally)?
If a seam looks wrong, re-check the sheets around that boundary
before going on. Seams are where merges and splits hide.

CHECKPOINT 4: no UNCLEAR remains in the notes; every student in
state.md has an identity or an honest "Student N" plus flag; seams
checked.

## Phase 5 - Write the grouping

1. Copy `templates/grouping.json` to `JOB/grouping.json`.
2. Fill it from your notes and state.md:
   - One entry per student, in video order. If a student has several
     booklets, all their pages go in that one entry, in video order.
   - `pages`: the times of that student's pages, one time per page:
     the FIRST frame time, then each NEW frame time. For a TWO frame,
     write its time TWICE (it carries two pages). Do not list SAME
     frames (extra views) or EMPTY frames anywhere.
   - Frame choice: for each page, list the time of its CLEAREST
     FOCUSED frame (the page alone, sharp, well lit). A spread frame
     may stand in for a page ONLY when that page never got a focused
     frame of its own; then flag that page "packaged from spread".
     Never package a blurry or spread frame when a clean focused
     frame of the same page exists.
   - `id` and `name`: exactly what you read in Phase 4a, or "".
   - `label`: "Student 1", "Student 2", ... in order.
   - `flags`: anything the teacher should know (identity uncertain,
     spread frames, a suspected missing page, very blurry page kept).
   - `unassigned`: every frame you could not place, with its time and
     a short reason. (EMPTY frames do not go here; they are counted in
     verification only.)
3. Read the file once fully before running the tool. Most packaging
   errors are typos caught by this one read.

## Phase 6 - Verify, then package

First the verification arithmetic. Compute these from your notes and
write all of them into state.md:

- F = total candidate frames (frames written, from Phase 1)
- P = number of page entries in grouping.json (all students together).
  A TWO frame is listed twice there, so it contributes 2 to P.
- T = number of TWO frames, from notes (each was listed twice in P,
  but it is only ONE candidate frame)
- S = SAME frames plus DUP frames (all extra views), from notes
- E = EMPTY frames, from notes
- U = unassigned entries in grouping.json
- RULE: (P - T) + S + E + U must equal F. If it does not, find the
  missing or double-counted frames in your notes and fix them. Do not
  package until this balances.
- PAGE RULE (just as hard): let D = the number of distinct pages in
  your "Distinct pages seen" list (all students together). Every one
  of those pages must be either packaged once, or written in the
  grouping as excluded with a reason (for example "blank page, no
  work on it"). A page that was seen but is neither packaged nor
  excluded means the run is NOT finished, even if the frame rule
  balances. Frame arithmetic cannot see a lost page. This rule can.
- Student count check: if the teacher told an expected count and
  yours differs, re-check every FIRST decision once. If it still
  differs, keep your result and add a flag in the report (Phase 7).
  Never force your count to match by inventing or deleting a student.
- Identity check: no two students share the same id, unless flagged
  "same id read twice - needs teacher decision" (Blocker B2 if the
  teacher must resolve it before grading).

Then package:

1. Run: `python3 tools/package.py JOB/index.json JOB/frames JOB/grouping.json JOB/out`
2. If it REFUSES: it lists the exact problems. Fix grouping.json only
   (never edit index.json or frames), run again.
3. Compare its printed totals with your verification numbers: students
   and total pages must match. Pages in the report = P (entries),
   because a TWO frame was listed twice and becomes two page images.

CHECKPOINT 6: verification balanced BEFORE packaging, and package
totals match.

## Phase 7 - Report and learn

1. Report to the teacher in this exact short format (fill the blanks):

```
Done. Video split into per-student PDFs.
Students found: N
Pages per student: S01: a, S02: b, ...
Identities read: X of N (list any "Student N" with unread identity)
Unassigned frames: U (reasons in manifest)
Flags: (list, or "none")
Output folder: JOB/out
```

2. Lessons. If anything in this run surprised you (a failure, a new
   video behaviour, a fix that worked), append ONE lesson to this
   skill's `LESSONS.md`, using its entry format. Rules for lessons:
   - General words only. No school names, no exam names, no student
     identities, no dates of one specific class.
   - Say what happened, what you did, what to do next time.
   - One lesson per surprise. If nothing surprised you, write nothing.

## Defined blockers (the ONLY reasons to stop and ask the teacher)

Ask mid-run only for these. Everything else: decide, flag, continue.

- B1: the teacher said every identity is required, and one or more
  identities stay unreadable after all zoom steps.
- B2: two groups carry the same identity and you cannot tell from the
  pages whether they are one student filmed twice or two students.
- B3: pages seem missing inside one student (for example visible page
  numbers jump and no frames cover the gap), and grading would be
  harmed. Ask whether to proceed with a flag or wait.
- B4: the video itself is unusable (no paper visible, or so dark or
  blurry that most frames stay UNCLEAR after bursts).
When you ask, always attach the evidence: the times, the crops, and
what you already tried. Never ask a bare question.

## Failure table

| What you see | Likely cause | Do this |
|---|---|---|
| frames.py: cannot open video | wrong path, or format the reader cannot handle | check the path by listing the folder; if the file exists, tell the teacher the format is unreadable (B4) |
| frames written far below duration | video shorter than expected, or reader failing mid-file | re-run once; check duration printed vs the file's real duration; if it repeats, B4 |
| Sheet cells black or labels missing | frames folder wrong, or sheets built from an empty index | confirm JOB/frames has images; re-run sheets.py with the exact paths |
| view.py: no frame at t | t is past the end of the video | use times from index.json, never invent times |
| package.py REFUSED | grouping mistakes (same time in two students, time with no frame, empty student) | fix exactly what it lists in grouping.json; run again |
| Everything is UNCLEAR | video quality too low for sheets | try smaller sheets: re-run sheets.py with `--per-sheet 9 --cell-w 640` for bigger cells; if still unclear, B4 |

## Worked mini example (fictional, only to show the shape)

A 9-second video. frames.py: duration 9.0, buckets 9, change
boundaries 4, frames written 11. One sheet of 11 cells.
Notes: t=0.5 FIRST (title page, identity field filled), t=1.0 SAME,
t=2.5 NEW, t=4.0 NEW, t=5.0 FIRST (new stack placed, identity field),
t=6.0 NEW, t=6.5 EMPTY (hand only), t=7.5 SAME, t=8.0 NEW,
plus 2 change frames coded SAME and EMPTY.
Pages: student 1 = 0.5, 2.5, 4.0 (3 pages). Student 2 = 5.0, 6.0,
8.0 (3 pages).
Verification: F=11, P=6, S=3, E=2, U=0. 6+3+2+0=11. Balanced.
Identities read from crops at t=0.5 and t=5.0. Package, report, done.

## If you are a weaker model, read this twice

- You do not need to be clever. You need to be careful and complete.
- The files remember for you: state.md, sheet_notes.md, grouping.json.
  Update them at every step, exactly where the phases say.
- Looking is your main tool. When in doubt, look at a bigger image
  (Phase 4) instead of thinking harder about a small one.
- UNCLEAR, unassigned, and "Student N" are honest answers. A made-up
  answer is the only real failure in this skill.
- Never skip a checkpoint. They are cheap. Mistakes found late cost
  the whole run.
