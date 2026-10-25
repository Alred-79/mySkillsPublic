# Spec: 3d-ui-optimizer

Status: drafted 2026-10-24, adversarially verified and revised the same day, evals and trigger evals written, RED baseline not yet run.
The repo's rule is evals and baseline before extensive skill text. This skill's text came first, so the baseline run is owed before it is called proven, and any baseline failure the text does not address is a required revision.
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

The craft engine for 3D, shader, motion, and interface visuals.
revamp-ui decides how much spectacle a site revamp gets. This skill decides how any visual gets built well at whatever intensity, and proves it by rendering.
It combines eleven sources into three mechanisms instead of concatenating them, because each source covers one layer and several contradict the official docs or each other.

1. The idea comes from the client's own material, since in taste-skill's own blind study its rule-driven builds tied or lost to the no-skill baseline in every round.
2. The cheapest technique tier that lands the idea, chosen with a recorded reason.
3. Look and measure before claiming, through a seekable clock, a capture script, and `V` ledger rows.

## Files

```
3d-ui-optimizer/
  SKILL.md                 # procedure, invariants, routing, ledger
  references/3d-craft.md   # Three.js and R3F art direction, budgets, frame loop, assets, R3F seek pattern
  references/effects.md    # liquid metal, folded gradient, liquid glass, particles, grain, hardening
  references/motion.md     # frequency rule, curves, component and page motion, GSAP, GSAP to 3D
  references/ui-craft.md   # constructive moves, type, color, variety, dated lint table
  scripts/seek-clock.js    # ?t=N freeze, reduced-motion still, off-screen pause, window.__ready
  scripts/capture.mjs      # Playwright captures at times, scroll positions, reduced motion, no WebGL
  evals/                   # evals.json, expected.md, trigger-evals.json, fixtures/ (foundry, laggy-scene, command-palette)
```

## Sources and what was taken

Read at the source level on 2026-10-24. Each line says what earned a place and what was cut.

| Source | Kept | Cut |
|---|---|---|
| collidingScopes/liquid-logo | The cosine-field loop and the tanh tone step that makes the chrome look, good preset values, the mask and NaN fixes | The page (it embeds analytics), the randomize ranges, `alert()` fallback |
| ruucm/shadergradient | The 1 by 192 ribbon plane, position-based color, the cropped camera, and the overrides that make the package shippable | The halftone grain pass, stock presets, its unmount-on-scroll lazy load |
| dashersw/liquid-glass-js | Rim-concentrated refraction math with an SDF-gradient normal | The architecture (static html2canvas snapshot, a context per element), so it is prototype-only |
| iart-ai/webgl-animation-skills | The seek and freeze capture idea, artifact triage, disposal facts, particle details | About 70 percent tutorial text, its CSS-pixel resolution and fixed-wait capture bugs |
| R3F docs, r3f-best-practices, three-best-practices, threejs-webgl, react-three-fiber, 3d-web-experience | Budgets, frame-loop rules, art direction, asset and VRAM rules, device tiers, with the conflicts listed at the end of 3d-craft.md resolved against the docs and library source | API listings, scaffolding scripts, phantom references, duplicated rules |
| freshtechbro/claudedesignskills (the rest of the stack) | The tier ladder, the preserve-3d flattening gotcha, one scroll owner and one writer, GPU memory math, designer-asset routing (Spline, Rive, Lottie) | About 95 percent, including engine API references, trend files, the purple gradient in its examples, user-agent sniffing |
| Leonxlnx/taste-skill | The study finding that orders the skill, the constructive moves, page-scale motion numbers, the variety mechanism | The old dials (revamp-ui owns dials), the creative-arsenal effect list, licence walkthroughs |
| pbakaus/impeccable | The detector as a lint engine, the font and theme procedures, the departure check, critique before detector output | Interview ceremony, generic heuristics, delight.md's cursor and confetti advice |
| emilkowalski emil-design-eng | The frequency rule, curves, durations, springs, interruptibility, component details, the Before After Why table | Philosophy prose and boilerplate |
| greensock/gsap and gsap-skills | About fifteen non-obvious rules, GSAP driving three, signature recipes, and a corrected horizontal-scroll example | Ease tables and API catalogues, routed to gsap-skills instead |
| mfranzon/render | The idea of marking a region on a rendered frame as feedback | Everything else. It is a CAD skill, and its local server executes posted code with no auth, so nothing is installed from it |

## Flow

0. Read the stack and the brand material, and size the job.
1. Find the idea in the subject, with the competitor test.
2. Pick the tier, recorded as a `V` row.
3. Build with the invariants, loading only the reference the work needs.
4. Make it seekable, capture, and read every frame.
5. Measure against budgets and run the lint after self-critique.
6. Report with the `V` ledger and a Before, After, Why table.

Ceremony scales, so a component change skips the ledger and the capture run.

## Evals and testing plan

Three cases that pull in different directions, so always doing more cannot win.

1. **foundry-signature-hero.** Creative. Constraint floor, process checklist, blind pairwise screenshots with revamp-ui's rubric, and a diversity check across reps.
2. **laggy-r3f-scene-fix.** Recall against 13 seeded defects with 5 clean decoys that must survive.
3. **command-palette-restraint.** The control. A keyboard surface used all day should lose motion and gain no 3D, while still getting a real craft improvement.

TDD cycle. RED is the no-skill baseline on all three, with the expected failures written in expected.md. GREEN is the with-skill arm beating it on each case's checklist at 3 or more reps on 2 model tiers.
Trigger evals live in trigger-evals.json, 10 should-trigger and 10 near-miss queries, with half the near-misses in revamp-ui's territory so the routing boundary is tested.

What has actually been run, all on 2026-10-24 with Playwright 1.64.1.
- capture.mjs against a raw WebGL shader page. All shots ready with no console errors, seeked frames differed, mobile at DPR 2, and the no-WebGL launch showed the poster. That first look caught a color miss (intended bronze rendered teal), the failure the skill exists to catch.
- After verification, the pages that broke version 1 (a resize right after the frozen draw, a late texture, CSS keyframes, a canvas starting below the fold, an unreachable URL) all capture correctly.
- The R3F seek pattern in 3d-craft.md on R3F 9.8. Seeked frames differed, reduced motion matched its still, and `__stats` reported real counts.
- The laggy-scene fixture builds and renders with no console errors.
The three eval cases themselves have not been run in either arm.

## Decisions

- 2026-10-24. Headless frame rate is reported as `unverifiable`. SwiftShader is a software renderer, so only counts and composition transfer from headless capture.
- 2026-10-24. Reduced motion is a designed still frame, not a kill switch. impeccable's `0.01ms !important` reset was rejected because it breaks scroll scenes and can leave content hidden.
- 2026-10-24. Lint runs after self-critique, following impeccable's own critique flow, so detector output does not anchor judgment.
- 2026-10-24. Ground truth lives in expected.md, never in fixture folders, so it cannot leak into the agent's workspace.
- 2026-10-24, after adversarial verification. R3F animation reads its own time ref instead of `state.clock`, because `setFrameloop` resets the clock and version 1's pause advice snapped scenes back to t=0.
- 2026-10-24, after adversarial verification. With a react-postprocessing composer, tone mapping is the last `<ToneMapping>` effect. The composer forces the renderer's tone mapping off, so version 1's renderer-only advice was a no-op, and D2 and D11 in case 2 were rewritten to match.
- 2026-10-24, after adversarial verification. seek-clock gained `whenReady` and a deferred redraw on resize, because version 1 drew a frozen frame once and a resize or a late asset left it blank while it still reported ready. capture.mjs now seeks CSS and Web Animations itself, because Playwright's `animations: 'disabled'` made every seeked CSS frame identical. Delta clamping now catches only outlier gaps, so slow devices keep real time.
- 2026-10-24, after adversarial verification. The preserve-3d rule now names every flattening property the verifier measured in Chromium and says to clip each flat layer separately, because version 1's "clip on an inner wrapper" also flattens.
- 2026-10-24, after adversarial verification. The trigger description narrowed premium and alive phrasing to one named component or interaction, because it collided with revamp-ui's description for whole-page requests.
