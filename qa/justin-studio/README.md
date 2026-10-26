# Justin studio integration — 2026-10-26

This incremental release replaces the retired `natural-v4` model in both `/​#pet` and `/​#meshy-review`.

## Source

- Body: `Justin_Mini_Shoulder_v39_Review`.
- Combined garment export: `Justin_Mini_Sailor_Vest_v22_Review.glb`.
- Published file: `public/assets/justin-mini/studio-v39/JustinMini.glb` (9,406,504 bytes).
- SHA256: `65611373ffda24a7cd352bc8e63066ff2ff7ad686151ee374114d266f707501b`.
- Five authored clips, 16 bones. The export is copied unchanged; facial shader and interaction adapters run in the app.

## Verification

- Actual pet page: model/version, five clips, vest equip/remove/reload persistence, sleep/wake, head/belly contact, ball surface collision.
- Actual review page: all five clips and front, three-quarter, both profiles, back captures.
- Desktop 1440×1000 and mobile viewport 390×844; no horizontal overflow; garment control at least 44px high.
- Isolated real-model fixture: mouth contact when feeding, six synchronized mouth morph primitives during speech, shader/morph closed-eye endpoint, disposal stops animation/voice and removes canvas.
- Existing interaction regression: `node --test --test-isolation=none qa/pet-interaction-effects.test.mjs qa/pet-interaction-engine.test.mjs` — 19/19 pass.
- Browser QA uses an isolated Edge headless context with software WebGL. This does not certify performance on a physical phone or microphone permission/recording on the user's device.
- Sleep initially floated over the bed. Support now samples source-space torso/head regions rather than tail/socket bone weights. A separate pillow supports the head. Captures were inspected again after the repair.

## Limits retained honestly

This is not full studio acceptance. There are five authored motions, not 24. Sleep is an app pose, not an authored sleeping clip. Wrist/finger roots, profile shading, shoulder seam, and garment edges still need art refinement. The old wardrobe meshes do not fit this model: outfit/hat/skin sales are temporarily hidden, inventory remains intact, and the compatible sailor vest has a free persistent toggle. Backgrounds, decor and food remain available.

The previous model and editable Blender/Meshy sources are preserved. No account, progress, backend configuration, or secrets are changed by this release.
