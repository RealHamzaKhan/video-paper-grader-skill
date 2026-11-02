# Lessons - video-paper-grader

Read this file fully at Phase 0 of every run.
After a run, append new lessons at the end, in this exact format:

```
## Lesson N - short general title
- What happened: (general words, no names of schools, exams, students)
- What fixed it / what to do:
- Applies when:
```

Rules: general words only. A lesson that only fits one video is a bad
lesson. Never write student identities or other private data here.

---

## Lesson 1 - Hand-held filming defeats stillness rules
- What happened: On hand-held video the camera never truly rests, so
  rules based on "the picture stopped moving" never fired and almost
  no pages were found, even though the pages were clearly visible.
- What fixed it / what to do: Never rely on stillness or small
  frame-to-frame differences to find pages. Take generous candidate
  frames (one per second plus change frames) and let the agent judge
  content by looking.
- Applies when: any hand-held or moving-camera video.

## Lesson 2 - Small OCR fails on handwriting at low resolution
- What happened: A free OCR engine read printed identities perfectly
  but failed on handwritten identities filmed at low resolution,
  including reading only part of a number. Making the crop bigger with
  contrast tricks did not fix it.
- What fixed it / what to do: Read identities by eye from enlarged
  full-frame crops (Phase 4a). Treat any OCR output as a hint to
  check, never as the reading. If the eye cannot read it either,
  label "Student N" and flag. Never guess.
- Applies when: handwritten identities, or video below about 1080p.

## Lesson 3 - A loose extra sheet can look like a new student
- What happened: An extra sheet carried its own printed header, very
  similar to a first page, and nearly started a false new student.
- What fixed it / what to do: Before accepting a FIRST, check the
  identity and the flow of work. Same identity plus continuing work
  means same student, whatever the header looks like.
- Applies when: students can add extra or loose sheets to their work.

## Lesson 4 - Layout similarity alone never proves a first page
- What happened: Blank and inner pages scored high on layout matching
  against a first page, because most of a page is white in both.
- What fixed it / what to do: FIRST needs the Phase 3 evidence rules
  (identity fields filled, or work clearly restarting). A page that
  merely looks like a first page is NEW or UNCLEAR, never FIRST.
- Applies when: all first pages share one printed layout.

## Lesson 5 - A sharp frame can still be useless
- What happened: A mid-flip frame won a sharpness contest while
  showing two half pages, and a frame of the empty desk formed its
  own "page".
- What fixed it / what to do: Sharpness only chooses candidates.
  Content decides. Expect EMPTY frames (desk, hands, mid-flip) in
  every real video and code them honestly.
- Applies when: always.

## Lesson 6 - Open books show two pages at once
- What happened: Booklets filmed open show a left and a right page in
  one frame. Counting the frame as one page loses a page; counting
  it as a new page breaks the order.
- What fixed it / what to do: Use the TWO code, count 2 pages, list
  the time twice in the grouping, and read left page before right
  page when checking content flow.
- Applies when: booklets, bound books, or sheets placed side by side.

## Lesson 7 - Filming style decides identity accuracy
- What happened: Identities filmed from far away, with the page
  filling only part of the frame, were much harder to read than the
  same writing filmed close.
- What fixed it / what to do: If a teacher asks how to film, suggest:
  page fills most of the frame, a short pause on each page, steady
  light, one page at a time where possible. This is advice only; the
  skill must still handle badly filmed videos as far as honestly
  possible, with flags instead of guesses.
- Applies when: a teacher asks for filming advice.

## Lesson 8 - A page can be shown twice
- What happened: A page that was already counted appeared again later
  in the video and nearly got counted as a new page.
- What fixed it / what to do: People flip back. If a frame's content
  matches an earlier page of the current student exactly, code it
  DUP: an extra view, zero new pages. Package each page once, from
  its clearest showing.
- Applies when: always; check for it especially when a "new" page
  looks familiar.

## Lesson 9 - Shaky video makes change frames multiply
- What happened: On a hand-held video, camera shake alone looks like
  "change" to a simple detector, so far more change frames were
  produced than on a steady video (about as many as the per-second
  frames).
- What fixed it / what to do: Nothing needed fixing. Extra frames are
  cheap; judge them as extra views. Do NOT raise change thresholds
  mid-run to reduce their number: a quiet, slow page turn could be
  lost that way, and a lost page is worse than extra frames.
- Applies when: hand-held or moving-camera videos.

## Lesson 10 - One student can have several booklets
- What happened: The same student appeared with two separate exam
  booklets plus an extra sheet. Each booklet had its own cover with
  identity fields, which looked like new students.
- What fixed it / what to do: A cover starts a new STUDENT only when
  the identity differs. Same identity = same student, new booklet:
  keep packaging into the same student, in video order, and flag
  "multiple booklets" in the report.
- Applies when: students can have more than one booklet, folder or
  bundle in one video.
