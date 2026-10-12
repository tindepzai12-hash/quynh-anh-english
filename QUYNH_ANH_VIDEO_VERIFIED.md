# Quỳnh Anh video — 2026-10-12

- Removed the learning profile form from Settings. Legacy profile route redirects to Settings; saved learning data remains intact.
- Added Quỳnh Anh directly after Account, with title `anh yêu em`, a large 16:9 player, fullscreen and replay controls, responsive layout and Nunito typography.
- Original 1280×720 video preserved. Deliverable is 2560×1440 QHD: light denoising, Lanczos upscale, conservative sharpening and contrast. This is an upscale, not recovered native 2K detail. Original audio copied without re-encoding.
- Final user revision: cut at 01:05, removing everything after that mark. Output: H.264/AAC, exactly 65.000 seconds, 75,938,942 bytes; faststart enabled. Full decode completed without errors. Browser metadata confirmed duration 65, 2560×1440; cache version `65s` avoids the former 71-second file.
- Local browser verified videoWidth 2560/videoHeight 1440, playback time advancing, fullscreen entry/exit, Settings form removal and sidebar order. At 390×844, no horizontal overflow; player retains 16:9.
- HTTP Range verified: 206, bytes 0–1023/82185318. Cloud media requires an existing signed-in app session; filenames are allowlisted, cache is private.
- Source syntax checks passed. QA screenshots: `qa/quynh-anh-2k/desktop.jpg`, `qa/quynh-anh-2k/mobile.jpg`.

No live learning progress or account configuration changed during QA.
