# Gemini and flashcard update — 2026-10-12

## Implemented

- Created a dedicated Google AI Studio key with the user's action-time confirmation. Stored only in ignored local environment configuration and Render environment variables. No billing enabled.
- Google model listing succeeded. `gemini-2.5-flash` generation returned 404; `gemini-flash-latest` returned 503 twice. Selected `gemini-3.1-flash-lite` from the returned model list and verified an actual text response.
- Actual Writing and Listening calls with original synthetic practice texts succeeded (2710 and 1198 response characters). Evidence: `artifacts/flashcard-gemini/live-api-test.json`. No private course PDF was sent.
- Added original versioned teaching guides in `tutor_knowledge.py`, a readable `/tutor-guide.html`, and explicit self-authored source fallback for general tutoring when cloud PDF retrieval is empty. Lesson-specific missing-source questions still fail honestly. These are not Huy Forum's prompts and do not impersonate him.
- Flashcard front/back share a fixed 620px desktop / 570px mobile outer frame. Meaning uses larger high-contrast Vietnamese text. Definition and expandable example stay in an internal scrolling panel. Ratings reserve space while hidden/inert before reveal.
- Prepared 570 per-card Gemini illustration prompts keyed by actual SRS ID, meaning and content hash. Generator is opt-in, resumable, stops on quota/access errors, limits each batch, and requires visual review before publishing. Frontend accepts only reviewed image manifest entries.

## Verification

- 12 Python tests passed, including tutor fallback provenance and refusal to invent missing lesson transcripts.
- 5 HTTP checks passed on isolated QA database: status, deterministic score, validation, Origin protection, missing AI configuration.
- JavaScript syntax checks and Python compilation passed.
- Browser checks at 1280px and 390px: card height unchanged on reveal; no horizontal overflow at 390px; no console errors. Native locator auto-scroll can shift viewport by 1px, while document coordinates and frame size remain stable.
- Screenshots: `artifacts/flashcard-gemini/desktop.png`, `mobile.png`. Existing topic art is still used where individual artwork is absent; it is not represented as newly generated Gemini art.

## Image blocker

The real `gemini-3.1-flash-image` request returned HTTP 429, with free-tier request quota limit **0**. No new illustration was produced. No billing was activated. The 570 requests are a queue, not 570 completed images. Cannot complete all individual images under the current account quota.

## VIL downloads

- Previous 7 downloaded PDFs remain verified in the local imports folder (554,648,313 bytes, 4475 pages including backup copies).
- Current authenticated UI exposes Premium status, no admin/export-all control. Collected 80 Cambridge Reading/Listening links and 188 VOL links through visible library controls. Saved locally under `imports/vil-english/research/`; clickable `exam-index.html` is an index, not downloaded exam bodies or answer keys.
- Cambridge 7 visibly says content not entered / coming soon. Cambridge library lists 15 books, but only books 12–21 exposed exam links during this inspection.
- Exam view exposes online questions, navigation, pause, notes and submit; no raw export was observed. No answers were submitted. No attack, privilege escalation or hidden API scraping was performed. Complete raw export remains dependent on legitimate owner/admin export access.

## Deployment

Render Free Node service remains in use. API key stays server-side. UI/data changes are packaged through the existing whitelist, excluding imports, learner databases, credentials and private source materials.
