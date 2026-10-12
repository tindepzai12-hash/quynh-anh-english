# Hallmark redesign and lesson video verification — 2026-10-12

## Changes

One shared ocean study system retains Nunito, existing routes, Google sign-in, account progress, individual vocabulary art and Justin. The home page now gives one primary continuation action, a daily learning agenda, skill index and flashcard/pet discovery. Courses use searchable chapter rows filtered by skill, purpose and duration. The shared rail, forms, focus states, spacing, reading surfaces and learning panels are aligned throughout the app.

Hallmark source: Nutlope/hallmark, commit 13ac0ec7e148655948100b6396439e481361d690. No new paid dependencies.

## Video recovery

All 52 original MP4s matched by normalized exact filename in the user's three Downloads ZIPs. Each recovered duration matched the catalog within 2 seconds. Web copies use H.264/AAC, up to 960 pixels wide and 12 fps, approximately 303 MB total. Originals are retained. A Reading frame was visually checked for legibility; this is an optimized lecture copy, not restored original resolution.

All 52 objects are in the private Supabase course-videos bucket. Upload verification checked HTTP 206, video/mp4 and 1024-byte partial responses for every object. Cloud playback requires the learner's signed-in session and uses expiring signed links. Active exam restrictions remain. Video files and secrets are excluded from Git.

## Midpoint checks

Every video lesson has one English A/B/C/D question at half its measured duration. Correct answers resume after a brief confirmation. Wrong answers show the selected misconception and correct answer, then resume on “Đã hiểu · học tiếp”. Answers persist; an answered check does not reopen automatically, but remains available for review. Seeking does not award watched progress.

Questions are editorial checks of each lesson's topic. They are not verbatim transcript extraction or a claim to summarize the exact words spoken at the midpoint. PDF-only lessons have no video checkpoint.

## Evidence

- `qa/hallmark-media.test.mjs`: 5/5 passing suites, covering 52 correct grades, 156 wrong-choice explanations, stale/invalid inputs, public answer-key redaction, persistence without watched-progress changes, and local range playback for 52 videos.
- Browser: actual Reading video playback; automatic question appearance after crossing halfway using the player keyboard; correct confirmation and automatic resume; wrong feedback and explicit continuation.
- Initial responsive audit: 72 route/width observations across 320, 375, 414, 768, 1440 and 1920 widths, in `responsive.json`. This audit preceded the midpoint dialog and final lesson layout correction.
- Subsequent visual correction: video/main column and chapter sidebar were reversed by a legacy grid placement rule; explicit grid placement fixes this. Mobile checkpoint typography was reduced after a 375-pixel screenshot showed an excessively tall title. The revised 375-pixel dialog displays all four options and submit button together.
- Screenshots in this directory document home, course browser, learning routes and midpoint/mobile checks. Some pre-final screenshots retain the earlier dialog title.

## Internal critique (1–5, not user testing)

Philosophy 4; hierarchy 4; execution 3; specificity 4; restraint 4; variety 3. The next lesson and route-specific workspaces are clearer. Execution remains 3 because legacy CSS/components still coexist and not every legacy interaction has received a full visual rewrite. No claim of 58/58 Hallmark gates or measured learning improvement.

## Limits

Lesson PDFs remain subject to their existing local/cloud availability. The complete source videos were duration-verified, not watched end-to-end by a human. Supabase free egress and Render free cold starts still constrain delivery. Real microphone and AI scoring are outside this increment's regression scope. Production deployment verification is recorded separately after publishing.
