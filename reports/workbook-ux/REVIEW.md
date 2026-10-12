# Lesson document and workbook UX review — 2026-10-12

## Observed before
Live Reading 3: the course list occupied roughly one third of the study area. The PDF was narrow, the draft sat beneath it, and source selection was duplicated. See before.jpg.

## Changes
- Documents are explicit cards with purpose, format, size, original link and in-page reading. Audio remains playable alongside its source.
- Practice pauses the video and hides the course list. Desktop shows the original PDF and saved draft side by side. Mobile switches between document and answers without discarding text.
- Three concise practice steps depend on Reading, Listening or Writing; original source instructions take priority.
- PDF supports page jumping and 125/150/200% zoom. Selected source and page resume within the browser session.
- Drafts retain existing version-checked autosave, explicit save and text export. Visible statuses distinguish saving, saved and error.
- Existing video checkpoint grading and lesson tracking are retained.

## Evidence and checks
- after.jpg: Reading 3 desktop, original PDF page 5 and a clearly labelled QA draft.
- mobile.jpg: 375px answer pane.
- Browser widths 320, 375, 414 and 768: no page-level horizontal overflow. PDF zoom may deliberately scroll inside the reader.
- Browser actions: saved draft, source switching, page jump, zoom, resource/practice round trip and reload retention. Verified an audio lesson and a PDF-only Writing lesson; no fabricated video player or completion.
- Node syntax checks passed for both changed scripts. Existing course-document and media tests: 7/7 passed on isolated QA data.
- Hallmark self-review: hierarchy and task separation improved; persistent secondary guidance is collapsed. These are internal observations, not a user study or measured usability score.

## Limits
This workspace stores free-text answers to original PDFs; it does not parse or automatically grade every PDF. Existing content gaps (empty deployed lesson quiz collection, unpublished Reading sets and online knowledge indexing) are not resolved by this UX change. All original source links are retained.
