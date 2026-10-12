# Design — học tiếng anh cùng bé iu QUỲNH ANH

## Direction
A welcoming study room for independent IELTS learners. Learning, not sales, drives each screen. One clear next action per workspace. Actual progress only.

## Genre and structure
Playful, restrained. Home: Ecosystem Index with one continuing lesson and a daily agenda. Course catalogue: Index-First, grouped by skill and course with purpose and duration filters. Content: video or exam workspace, split into study surface and tools. Pet: original room and shop. N3 side rail shared throughout. Compact legal footer.

## Typography
Nunito locally hosted, retained as expressly requested. Display 800–900, body 400–700; roman headings, no font swaps per page. See public/tokens.css.

## Theme
Ocean blue actions, deep navy navigation, almost-white paper. Soft mint and sand only on contextual learning invitations. All new colors named as OKLCH tokens. public/tokens.css is the executable palette.

## Spacing and interaction
4px scale, 46px primary targets, visible focus ring. 16px cards; 24px main surfaces. Navigation remains consistent across pages; icons collapse only at intermediate sizes. Mobile uses the existing accessible menu. Transform/opacity only; reduced motion removes movement. No entrance animation on study controls.

## Ownership
Existing authentication, drafts, timers, assessment, media progress and pet controllers retain their responsibilities. No invented bands, testimonials or completion metrics. Lessons without a video remain clearly identified as PDF lessons.

## Exports
Browser tokens: public/tokens.css. This vanilla project uses these directly rather than introducing Tailwind or shadcn packages.
