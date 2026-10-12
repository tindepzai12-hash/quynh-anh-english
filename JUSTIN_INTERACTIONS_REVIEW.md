# Justin Mini interaction release — 12 October 2026

## Scope
Real Three.js interaction props and mesh picking, without changing the exported character identity or authentication engine. Existing natural-v4 GLB and 17 animation clips are reused. This release does not include the separate Reading work in progress.

## Implemented
- Five explicit modes: pet, belly tap, throw, feed, rotate; keyboard alternatives and contextual instructions.
- Rounded 3D hand follows head strokes. Belly fist approaches before contact; reaction begins at contact, followed by recovery. Cooldown prevents accumulated belly hits; only one head request can queue.
- Ballistic throw with actual animated-mesh collision, rebound and misses. Face regions distinguish left/right cheek, forehead, central nose/chin. Raised bruise meshes and local head-vertex displacement follow animated triangle anchors and fade after seven seconds; at most four patches.
- Eight food definitions and original SVG tray/shop art. Only owned items appear in tray. Outside-mouth drag does not consume inventory; successful server use consumes one item and starts bite/shrink/chew. Existing keyboard/shop feeding remains available.
- Structured local emotion priorities, short memory and fullness; this is deterministic gameplay, not an AI emotional model.
- Original synthesized reaction sounds, initially muted, with explicit toggle. No microphone permissions requested for this QA.
- Bed supports torso, separate pillow supports head; tail rig lifts during sleep and restores on wake.
- Listening practice action label changed to “Nghe”. Voice-recording replay labels remain appropriate.

## Visual iteration and evidence
Workspace evidence: `artifacts/justin-interactions-20261012/` (not published with learner screenshots).
1. Initial reach angle left the arm too low for cheek contact. Increased bounded shoulder reach and captured new left-cheek reaction.
2. Mobile controls covered the belly because a later stylesheet overrode stage height. Added last-loaded interaction stylesheet; final 390px shot exposes full character body.
3. Initial sleep review showed tail penetrating the bed. Added reversible Tail_Base pose correction; `justin-release-sleep.png` shows raised tail and torso on mattress.
4. Six outfit combinations captured specifically at `effectPhase=reaction`: school, explorer, pajamas, sport, scarf, cap with scarf. `justin-release-outfits.jpg` assembles the actual screenshots. No prominent detachment observed at this sampled pose; this is not proof for every animation frame.

## Verification
27 automated checks passed in the isolated release package: 19 rig/physics/cleanup/reduced-motion/bed tests, 4 food backend tests, 4 HTTP account/privacy/persistence regressions. Tests load the real GLB geometry/rig, stripping texture references for Node-only geometry checks.
Browser QA on isolated SQLite at localhost:8769: belly contact timing, ball contact, feeding 3→2 berries, sleep/wake, six outfit reaction poses, reduced-motion app setting, sound toggle state, navigation during an action and return with one canvas. No captured console errors/warnings in these flows.
Final viewport observations: 390×844, 768×1080, 1440×1080, 1920×1080; scrollWidth did not exceed innerWidth. Mobile testing used a desktop browser viewport and pointer, not a physical phone.
Source QA in the preceding work also verified actual left/right hits, a miss without a bruise, outside-mouth drop preserving food, and direct head strokes.

## Limits
This is additive animation on the existing rig, not newly authored cinematic motion or a new Blender sculpt. Face expressions reuse existing morphs; no phoneme rig was created. Sound toggle and synthesis exercised, but subjective speaker quality is not certified. No sustained frame-rate benchmark or physical touch-device test was performed. Optional sophisticated food preferences and a long-term pet personality are not implemented. The exact 2D likeness and appeal still need human art review. Backgrounds remain 2D around the 3D character. Gemini image generation is a separate pending task, previously blocked by image quota; no billing changes were made.

## Deployment
Isolated branch based on deployed main 1818255, preserving unrelated Reading changes and all learner databases. No secrets, SQLite files, or reference-account screenshots are included. Live status must be checked after the push before calling the deployment complete.
