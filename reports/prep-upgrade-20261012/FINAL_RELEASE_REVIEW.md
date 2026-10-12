# Release review — 12 October 2026

This record supersedes the earlier deployment/QA status for this increment. It does not claim that every long-term item in the PREP master prompt is complete.

## Vocabulary

- All 570 vocabulary entries have an individual decoded image, visually inspected in labelled review sheets.
- Release asset validation: 570 reviewed WebP mappings, zero missing images, invalid paths, undecodable files or identical byte duplicates. Total 60,452,664 bytes; images load individually rather than as one page payload.
- Incorrect literal idiom scenes were replaced during review. Each card retains its textual definition; pictures are memory cues, especially for abstract meanings.
- Image release `0bdb427` was confirmed live by Render. Live `folk songs` card loaded its 768 px image; the answer retained the card structure. The 390 px page had no horizontal document overflow.

## Study improvements merged

- Reading font and pane-width preferences, versioned passage notes, practice pause/resume and review filters.
- Worker failure recovery without replaying uncertain mutations.
- Source paragraph/table preservation and manual content correction form.
- Versioned Listening drafts, browser recovery and server-scored attempt history. Reopening the same local audio retains the draft.
- Dashboard continuation/review suggestions and per-type Reading results from saved attempts; no invented proficiency or band.
- Speaking preparation countdown, recording pause/resume/error cleanup. Existing recording-ready events for Gemini were preserved.
- Writing feedback shows the submitted text alongside the current text when they differ.
- Existing personal tutor, Google login, fixed lower-right Justin launcher, removed profile form and Quỳnh Anh video were preserved during the merge.

## Verification

- 80 Reading engine/import/source/privacy checks passed on the actual release code with isolated temporary state and local source catalogue.
- 6 Reading focus tests; 2 Listening persistence tests; 2 worker recovery tests; 2 HTTP study-flow tests; 8 account/OAuth tests passed. These are 100 checks/tests of mixed granularity, not a coverage percentage.
- First attempts failed because sandbox SQLite could not open temporary directories and the account suite targeted a stopped 8766 server. Re-running with permitted temporary access and the isolated 8769 server passed. An initial release source test had no local catalogue; re-running with the existing private local catalogue passed. No production account was modified by these tests.
- Browser Reading: answer, flag, font 20, note, pause, reload, resume, submit and filtered review. Answer, note, font and paused state survived reload. Submission produced 1/40 against source keys for the deliberately minimal QA attempt.
- Browser Listening: edit, autosave confirmation, compare, reload and exact text restoration. Speaking preparation countdown displayed correctly; no real microphone permission was accepted.
- Six routes at 390×844, 768×1024, 1440×900 and 1920×1080: 24 observations, no horizontal document overflow. Desktop and mobile Reading screenshots were inspected after layout transitions settled.
- JavaScript syntax checks passed for changed Reading, Listening and ecosystem scripts.

Evidence: `final-evidence/responsive.json` and the Reading/Listening/Speaking screenshots. Image review evidence is retained locally under the parent project's `artifacts/antigravity-flashcards/review-evidence/`.

## Remaining product work

Additional Reading editions still need source/key editorial approval; draft content is not auto-published. Dedicated categorization rendering, complete 40-question Listening exams, verified transcript timestamps and a full Speaking mock remain broader prompt items. Real microphone capture and live AI feedback were not re-tested in this isolated increment. No arbitrary ≥90 design score or fabricated user test is assigned.

Deployment of these study changes must be confirmed separately after the commit; successful local QA alone is not proof of a live release.
