# Video Paper Grader (agent skill)

Turn ONE long video of paper work into one clean PDF per student.

A teacher films flipping through a whole class's papers, booklets or
notebooks, page by page, in a single video. An AI agent follows this
skill to split the video into per-student PDFs: it extracts candidate
frames, packs them into labelled contact sheets, judges the structure
itself by looking, reads each student's identity by eye, verifies the
counts, and only then packages the files.

The design rule: **the agent is the judge, the scripts are only
hands.** Nothing about the video is assumed: not the school, exam,
paper layout, language, identity format, page count, video length or
filming style. The skill is written in tiny explicit steps with
templates and decision tables, so weaker models can run it well too.

Grading the work is a separate step and is not part of this skill.

## What is inside

- `SKILL.md` - the full instructions the agent follows (Phases 0-7,
  checkpoints, verification arithmetic, defined blockers)
- `LESSONS.md` - the skill's memory: general lessons from past runs,
  read at the start of every run, extended after every run
- `tools/frames.py` - clearest frame per second + change frames
- `tools/sheets.py` - labelled contact sheets from candidate frames
- `tools/view.py` - full-size frame, identity crop, or burst sheet
- `tools/package.py` - builds per-student folders + PDFs from the
  agent's grouping file (refuses inconsistent groupings)
- `templates/` - state.md, sheet_notes.md, grouping.json

## Install (Mac or Linux)

```bash
git clone https://github.com/RealHamzaKhan/video-paper-grader-skill.git
cd video-paper-grader-skill
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Needs only Python 3 with OpenCV, NumPy and Pillow. No API keys, no
internet calls, no paid services. Student work never leaves the
machine except to the agent you choose to run.

## Use it with an agent

Option A, skill-aware agents (for example Claude Code):
copy or symlink this folder into the agent's skills folder, e.g.

```bash
mkdir -p ~/.claude/skills
cp -R video-paper-grader-skill ~/.claude/skills/video-paper-grader
```

then ask the agent to use the video-paper-grader skill on your video.

Option B, any agent (Cursor, Codex, Claude, others):
open this folder in the agent and paste this prompt, filling the
paths:

```
Read SKILL.md in this folder and follow it exactly, phase by phase.
Also read LESSONS.md first, as Phase 0 requires.
Video: /path/to/your/video.mp4
Job folder: /path/to/job-folder
Use the python in .venv of this skill folder to run the tools.
Do not skip checkpoints. Show me the Phase 7 report when done.
```

Whichever model you use: the skill makes the agent write its state
and notes to files as it goes, so a run can be stopped and resumed,
and every decision can be checked afterwards.

## Filming tips (for the teacher)

- Hold each page steady for about 2 seconds.
- Let the page fill most of the frame; identity text reads far better
  when filmed close.
- Steady light, avoid strong shadows on the page.
- Badly filmed videos still work as far as honestly possible: the
  agent flags what it cannot read instead of guessing.

## Status

Tested end to end on a synthetic class video (4 students, 12 pages,
all identities correct against ground truth) and on a real hand-held
phone video of marked exam booklets (1 student, two booklets plus an
extra sheet, 15 distinct content pages, all 92 candidate frames
accounted for in verification). A full-length class video and a
deliberately weak model are the next tests.
