# Expected: ground truth per case

Run with-skill against a no-skill baseline, at least 3 reps per arm, at least 2 model tiers, per docs/specs/evidence-protocol.md.
Never golden-output matching for case 1. Cases 2 and 3 are scored against the tables below.
The fixture folders hold no answers, so nothing here leaks into the agent's workspace.

---

## Case 1: foundry-signature-hero (fixture: foundry)

A plain landing page for a fictional bronze foundry, with no three.js, no build step, and an inline SVG mark.

**Subject material already on the page.** Sand casting at 1,150 °C, cooled in the mold overnight. One heat a day, about 40 pieces, a 1931 crucible furnace. An unlacquered patina that brightens where hands touch it. Solid bronze still on old-town doors. A bold circular H mark as SVG.

**Seeded slop.** `#6366f1` button, 12px soft radius on buttons and cards, a centered "Welcome to" hero followed by three identical cards, emoji icons, the system font stack, uniform card shadows.

**Load-bearing.** The four nav routes, title and meta description, the footer address, and every factual claim in the copy.

**Traps.**
- The category reflex. A floating torus, icosahedron, or particle field with a violet or blue gradient from a CDN fails the competitor test.
- The unearned tier. Pulling in three.js for an effect one full-screen triangle or CSS can do.
- Blank degraded states. A canvas with no poster, nothing under reduced motion, or an `alert()` on missing WebGL.

**Scoring.**
1. Constraint floor, binary. Renders with no console errors, load-bearing content intact, responsive at 1440 and 390, contrast 4.5:1 on the headline over the effect, reduced-motion and no-WebGL frames are designed.
2. Process checklist from evals.json, scored per expectation.
3. Blind pairwise screenshots against the baseline arm using revamp-ui/evals/judge/pairwise-rubric.md, with Creative Distinction scored and Prompt Adherence keeping distinction tied to this client.
4. Diversity across reps. Extract the signature effect, type families, and palette from each rep. The same effect and type across all reps means the skill collapsed into a template.

**RED baseline expectation.** The no-skill arm usually adds three.js from a CDN with a rotating primitive or particles under default lighting, uncapped DPR, a loop that never pauses, no poster, nothing for reduced motion, and a claim that it looks great with no capture.

## Case 2: laggy-r3f-scene-fix (fixture: laggy-scene)

A small R3F product page for a fictional water bottle, runnable after `npm i && npm run dev`.
Verified 2026-10-24 with `vite build`, `vite preview`, and capture.mjs. It renders with no console errors and shows the seeded look (flat light, everything glowing, a grey ground). It reports NOT-READY because the before-state has no seek clock, which is part of what the skill should add.

### Seeded defects (recall)

| id | Where | Defect | Expected fix |
|---|---|---|---|
| D1 | App.jsx Canvas | `dpr={window.devicePixelRatio}` renders at DPR 3 on many phones | `dpr={[1, 2]}`, 1.5 on mobile, or PerformanceMonitor |
| D2 | App.jsx lights and composer | `ambientLight` 0.5 plus one directional at 1 and no environment, the flat default, and an `<EffectComposer>` with no ToneMapping effect, so the scene renders untonemapped (the composer forces the renderer's tone mapping off) | Self-hosted environment map, one key light, and `<ToneMapping mode={ToneMappingMode.NEUTRAL} />` (or AGX) last in the composer. Setting tone mapping on the renderer alone is a no-op here and does not count |
| D3 | App.jsx Bloom | `luminanceThreshold={0}` makes everything glow | Threshold about 1, the glowing cap `toneMapped={false}` with values above 1 |
| D4 | App.jsx ground | Real-time shadow map on a grey plane | ContactShadows with `frames={1}` or a baked plane |
| D5 | App.jsx and ScrollCamera.jsx | `frameloop="demand"` while GSAP mutates the camera and the backdrop's opacity and nothing calls `invalidate()`, so the camera freezes | `invalidate()` in each tween's `onUpdate`. Switching to `frameloop="always"` hides the bug and does not count |
| D6 | ScrollCamera.jsx | `camera.lookAt` in `scrollTrigger.onUpdate`, which stops while scrub is still catching up | Derived updates in the tween's `onUpdate` |
| D7 | App.jsx and ScrollCamera.jsx | OrbitControls with damping and the scroll tween both write the camera | Disable controls during the story, or tween a rig the controls do not own |
| D8 | Bottle.jsx | `setT` inside useFrame re-renders React every frame | Read time from `state.clock`, no state |
| D9 | Bottle.jsx | `new THREE.Vector3` inside useFrame allocates every frame | Hoist a temporary and `.set()` it |
| D10 | Bottle.jsx | `lerp(..., 0.1)` is frame-rate dependent | `1 - Math.exp(-λ * delta)` or `damp` |
| D11 | glowMaterial.js | `uResolution` in CSS pixels while `gl_FragCoord` is in device pixels, so the cap's gradient doubles on DPR 2 screens | Drawing-buffer size (`gl.getDrawingBufferSize`), updated on resize. Adding the tone mapping and color space includes is fine but optional, since under the composer they are no-ops |
| D12 | styles.css `.tilt` | `overflow: hidden` on the `preserve-3d` element flattens the translateZ layers | Move the clip and radius to the photo layer itself (or a wrapper around the photo alone that carries its translateZ), keeping the photo and label as direct children of `.tilt`. A wrapper around both layers stays flat and does not count |
| D13 | Badge.jsx | A second `<Canvas>` opens another WebGL context and always-on loop for a 96px badge | drei `View` on the main canvas, or CSS or SVG |

### Clean decoys (must survive)

| id | Where | Why it is correct |
|---|---|---|
| C1 | Bottle.jsx | `THREE.MathUtils.damp(..., 4, delta)` on the cap is frame-rate independent. Its target reads `t`, which changes with D8, but the damping is right |
| C2 | Bottle.jsx | Geometry and material in `useMemo` are shared correctly |
| C3 | Bottle.jsx | The price label in drei `<Html>` keeps accessible DOM text |
| C4 | ScrollCamera.jsx | `transparent = true` is set before tweening the backdrop's opacity (its missing `invalidate()` belongs to D5, not to this row) |
| C5 | styles.css | The reduced-motion block is correct and should be extended, not removed |

**Scoring.** Recall is the share of D1 to D13 found and fixed. False positives are any C row flagged or broken. A fix that changes the bottle color, copy, or price is a regression.
Findings outside the seeded list are not penalized when they are real, such as the cleanup that kills only the trigger and not the tween.

**RED baseline expectation.** The no-skill arm usually caps DPR and maybe removes the setState, misses the invalidate freeze or patches it by switching to `frameloop="always"` (which hides the bug and keeps the battery drain), keeps threshold-zero bloom or lowers intensity instead, and does not notice the preserve-3d flattening or the second context.

## Case 3: command-palette-restraint (fixture: command-palette)

A React command palette opened from the keyboard many times a day.

### Seeded over-motion

| id | Where | Problem | Expected |
|---|---|---|---|
| M1 | `.palette` | 400ms `ease-in-out` open from `scale(0)` on a 100+ times a day, keyboard-triggered surface | No open animation, or a sub-100ms opacity change at most |
| M2 | `.item` | `transition: all 300ms` | Transition named properties only, or none |
| M3 | `.item:hover` | Lift and shadow on every list row | Background change only, gated to `(hover: hover) and (pointer: fine)` |
| M4 | `.item.active` | Keyboard selection animates with an overshoot curve and scale | Instant state change |

### Clean decoys (must survive)

| id | Where | Why it is correct |
|---|---|---|
| K1 | `input:focus-visible` | A visible focus ring |
| K2 | `.toast` | 180ms ease-out entry on an occasional surface |
| K3 | reduced-motion block | Correct, extend rather than remove |

**Trap.** The prompt invites glass or 3D. Adding WebGL, a canvas, or decorative glass to a utility surface is a fail, and so is shipping nothing, since premium here means speed and precision with a real type, spacing, or active-row improvement.

**RED baseline expectation.** The no-skill arm usually keeps or lengthens the open animation, swaps in a spring, adds a glass backdrop, and makes hover richer, which makes the palette feel slower.
