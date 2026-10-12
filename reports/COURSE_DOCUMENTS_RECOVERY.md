# Course documents recovery — 2026-10-12

## Recovery

- Matched all original non-video catalog entries by full archive-relative path and exact original size, avoiding duplicate-basename mistakes.
- Recovered 72 PDFs from the course ZIP, then 18 PDFs from the British Council RAR: 90 PDFs total, 4 MP3, 1 M4A and the original RAR (96 resources, 132,847,524 bytes).
- Uploaded to the private `course-documents` bucket. Each upload was checked through a signed URL and a 1,024-byte Range request. Manifest contains resource IDs, hashes and sizes; no credentials or local paths.
- The screenshot's BAI TAP LUYEN TAP and SLIDE BAI GIANG MULTIPLE CHOICE are r101/r108, Reading lesson 3. Their original contents are preserved.
- Related Writing documents are labelled as material from the combined course; no unrelated source is presented as an exact match.

## Learning flow

- Every lesson has a post-video practice entry. The video `ended` event updates its invitation; learners can also open practice earlier.
- Workbook shows the source PDF/audio and saves numbered free-text answers separately from notes and watched progress. Field versions reject stale overwrites.
- PDF.js 4.10.38 (Apache-2.0, vendored license) replaces the browser PDF plugin that appeared black in the in-app browser. Previous/next and direct page navigation are available.
- Existing source-checked interactive quizzes remain below the workbook. Restored PDFs are not falsely advertised as fully converted or automatically graded.
- Media requires login online; support files remain blocked during an active exam, and raw answer PDFs remain protected.

## Verification

- QA isolated database, localhost:8769: 7/7 document/media/midpoint tests passed. Checked all 96 catalog resources, protected answer IDs, Range delivery, workbook persistence/conflicts, and all 52 midpoint checks/video files.
- Browser: source PDF rendered (177-page Multiple Choice workbook); answer saved, reloaded and restored. Listening sources also opened.
- Workbook at 320/375/414/768 px: no document horizontal overflow in DOM measurements. Viewport override reset.
- Production verification recorded after deployment below.
