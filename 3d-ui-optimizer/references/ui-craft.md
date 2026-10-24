# UI craft, from the idea to the lint pass

Load this for any page or component, with or without 3D.
The moves come from taste-skill's blind study and critique notes, impeccable's references and detector, and emil-design-eng, read 2026-10-24.
The finding that orders this file is taste-skill's own result. Pages built from bans alone tied or lost to no skill at all (6.9 against 7.9 on unseen briefs), while the judges rewarded an idea that belonged to the client, one live thing, full content at a readable size, and one dominant element on the first screen.
So the constructive moves come first and the bans run last, as a lint.

## Contents

- Constructive moves
- Type
- Color
- Variety across projects
- The lint pass (dated)

## Constructive moves

1. **List what only this client has.** Eight to twelve facts, such as what the name means, the street, the numbers, the one constraint it lives with, its materials, its rituals, the printed things of its world.
2. **Write the idea as a sentence.** "On this page, [a thing from the list] becomes [a device]." Swap in the nearest competitor's name. If the sentence still works, it is a category idea, so go back to the list.
3. **Sections are claims.** One claim per section, each with its proof. Delete any section without a claim. This is what kills the stock hero, logos, features, testimonial, pricing order.
4. **Carry the idea to the end.** Pricing, FAQ, and footer get the idea too. A distinctive hero followed by stock blocks is the most common failure, even among strong sites.
5. **One layout word per section.** Write a single word for each section's layout. The same word twice in a row means the template is showing.
6. **Break the system once, on purpose.**
7. **Fill removed ornament with substance.** Scale, real content, a picture, or a flat color field, never another ornament. A page made empty by removing tells is itself a tell.
8. **Real pictures.** Four or more real raster pictures on a marketing page (canvas and SVG do not count), of the subject's world, with one treatment for all and two aspect ratios for most. A picture either fills 60 percent or more of its screen or stays under 10 percent.
9. **App screens get a face.** A ground tinted from the product's world or its hue on the main data element, one element only this product has, and one question and one finding per screen. Totals are computed from the rows, so the data adds up.
10. **3D earns its place.** Canvas-heavy pages scored higher in the study, but pages drawn only in canvas scored lowest, a 3D gallery lowered scores, and loading screens gained nothing. So the HTML first screen is readable on frame one and the scene fades in behind it.
11. **Pick the theme from a scene sentence.** Who uses it, where, in what light, in what mood. Light or dark follows from that, not from fashion.
12. **Choose fonts by procedure.** Write three voice words. List the three fonts you would reach for by reflex and reject them. Look for the type as a physical object from the client's world, such as a museum caption, a 1970s terminal manual, or a seed-packet label. If the final pick matches a reflex, start over.

## Type

Settle by register.

| | Brand and marketing | Product UI |
|---|---|---|
| Sizes | 2 or 3 working sizes, 5 at most, display at least 4 times body | Modular scale at 1.125 to 1.2 |
| Body | 17 to 19px | 14 to 16px, nothing under 12px |
| Display | line-height 0.95, tracking -0.02 to -0.05em, `max-width: 14ch`, `text-wrap: balance`, optical pull about -0.05em on the left edge | Tight leading only on headings, 1.3 or more on text |
| Headlines | 2 lines or fewer at 1440, 768, and 390 wide, about 32 characters | One line where it can |
| Huge type | 72px or more only for strings under 40 characters | Never |
| Families | One family is normal and fine. A second only with a reason | One family, tabular numbers on data |

Line length stays near 65 to 75 characters.
Section gaps run 120 to 240px on brand pages and 48 to 96px in product UI.

## Color

- Roles are ground, surface, ink, muted, accent, and accent-ink. Ground covers 70 to 90 percent of the screen.
- Surfaces separate from the ground by a 2 to 6 point lightness step, not by lines or shadows.
- Accent stays under 5 percent of any screen, about 3 percent on app screens. A committed or drenched brand color belongs to one deliberate hero, not the whole site.
- Change the section color per chapter with hard cuts, and neighboring colors differ in lightness.
- `#6b6b6b` is the lightest gray that passes 4.5:1 on white.
- One hue per chart where possible. Over 4 hues warns, over 6 fails.
- Buttons are square or pill, decided once. In the study 52 percent of top sites used square, while 59 percent of weak sites used pill, and the 9 to 16px soft radius was the weak-site default. Picture corners are square.

## Variety across projects

A model returns to its favorites, so variety needs a mechanism.

- When generating directions, label each with one design-family noun. If two share a noun, rework one. Then write one sentence per direction, and if two sentences rhyme, rework.
- Never pick directions from a fixed list. Models pick Swiss grid, terminal, and industrial signage every time.
- Keep a short history of your own choices (type system, palette, hero shape, signature effect) in the user's taste profile (see revamp-ui and docs/specs/evidence-protocol.md), and avoid repeating the last few on a new project unless the brief asks for it.

## The lint pass (dated 2026-10)

Run this last, after your own critique, so detector output never anchors the design judgment.
If impeccable is installed, run `node <impeccable>/scripts/detect.mjs --json <files>` (exit code 2 means findings).
If taste-skill is installed, run its `scripts/lint.mjs` and `scripts/inspect.mjs`.
Then check what both miss.
Font and hex lists go stale within months, because every "use this instead" list becomes the next tell, so treat the table as dated data.

| Tell | Threshold |
|---|---|
| Default indigo and violet | Hue 235 to 310 on any theme color. Tailwind `#6366f1` sits near 239, below both detectors' ranges, so check it here |
| Eyebrow label above a heading | One above the h1, or three or more on section headings |
| Index numbering 01, 02, 03 | Any sequence used as decoration |
| Monospace outside code | Any |
| Cream with terracotta | Cream at HSL hue 22 to 62, saturation 0.16 or more, lightness 0.88 or more, with terracotta at hue 6 to 30. Tokens named paper, bone, or linen are a tell too |
| Tiny tracked uppercase labels | 14px or less at 0.05em or more tracking, three or more |
| Colored side stripe on cards | 2px or more with a radius |
| Icon tile stacked on a heading, nested cards | Any |
| Gradient text, glass card grids, uniform shadows | Unless the brief sanctions them |
| Em dashes in copy, buzzwords, "Not an X. Y." cadence | Five or more em dashes, three or more cadence hits |
| Overshoot easing, `transition: all`, ease-in, `scale(0)` | Any |
| Parallax travel | Over 8 percent |
| Content hidden by motion | h1 unreadable 1.2s after load, or two or more first-screen texts invisible under reduced motion |
| Custom cursor | Any, unless the brief is a playful experience and reduced motion restores the system cursor |
| Placeholder copy | Any |

Accessibility holds at every intensity. Text contrast 4.5:1 and large text 3:1 checked against the real background (for text over images or canvas, against the brightest region behind it), visible focus, keyboard reach, and 44px touch targets.
