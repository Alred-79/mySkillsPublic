---
name: 3d-ui-optimizer
description: "Art-directed 3D, WebGL, shader, and motion work for the web, checked by rendering it. Use for any Three.js or React Three Fiber (R3F) scene, a GLSL or WebGL effect (liquid-metal logo, animated shader gradient, liquid glass, particles, grain), GSAP or scroll-driven 3D storytelling, a 3D hero or signature animation, and the motion and feel of one named component or interaction (a modal, dropdown, menu, hover, or transition). Also use it when an existing scene or animation is slow, janky, laggy on phones, flat, washed out, or over-glowing, in preference to generic Three.js best-practice lookups, because it diagnoses against measured budgets and fixes the art direction too. It finds the signature idea in the client's own material, picks the cheapest technique that lands it, builds with performance budgets and reduced-motion and no-WebGL fallbacks, then freezes frames, screenshots desktop and mobile, and measures draw calls before calling it done. Trigger phrasings: \"add a 3D hero\", \"make our logo liquid metal\", \"animated gradient background\", \"liquid glass nav\", \"this R3F scene is laggy\", \"why does my Three.js scene look flat\", \"make this animation feel better\", \"scroll-driven 3D story\", \"this dropdown feels cheap\". To redesign, restyle, or modernize a whole existing site or page, or make it feel modern, premium, or alive overall, use revamp-ui, which can route its craft here. Not for backend work."
---

# 3D UI optimizer

Make the visual belong to this product, build it the way it holds up on a real device, and look at the rendered frames before saying it works.

## Why this works (read first)

Asked for a 3D hero, a capable model ships a spinning primitive under `ambientLight` 0.5 at fov 75, an uncapped pixel ratio, a loop that renders 60 times a second forever, a violet gradient, uniform 300ms ease-in-out, and no plan for reduced motion or a failed WebGL context.
Then it says the result looks great without having seen a single frame.
Three mechanisms carry this skill, and everything else serves them.

**The idea comes from the subject.** In taste-skill's own blind study, its rule-driven builds tied or lost to the no-skill baseline in every round, even with far fewer detector failures. What the jurors rewarded was an idea only this client could own and one live thing. So the signature moment is bound to the client's material, its logo, its product, its data, its process, and the bans run last as a lint.

**The cheapest technique that lands it.** Most signature moments do not need a 3D engine, and the ones that do need the engine's defaults replaced. Choosing the tier is a decision with a recorded reason, not a reflex toward Three.js.

**Look and measure before claiming.** Every animated visual runs from one seekable clock, so exact frames can be captured and compared. The skill screenshots its own output across viewports and degraded modes, reads the images, and reports measured counts. A claim about how it looks or performs without a capture behind it is a finding, not a pass.

Ceremony scales to the task. A one-line easing fix gets the fix and a Before, After, Why row, not a ledger and six steps.

## Routing

This skill owns the idea, the technique choice, the art direction, the architecture invariants, and the verification.
It routes deep API detail and adjacent loops instead of repeating them.

- **gsap-skills** for GSAP API detail. **r3f-best-practices** and **three-best-practices** for rule lookup beyond `references/3d-craft.md`. Where they conflict, prefer these references, which were checked against the official docs and library source in 2026-10 and list the known conflicts in 3d-craft.md. Version-sensitive rows go stale, so check the library source when a major version changes.
- **impeccable** and **taste-skill** as lint engines in step 5, when installed. **emil-design-eng** for a deep motion review of a component.
- **revamp-ui** when the user wants a whole existing site redesigned and the intensity is not settled. Its contract sets how much. This skill decides how.
- **adversarial-verify** as an optional closer on the `V` ledger.

If something important turns up outside this lane, say it in a line and point to the right skill.

## Procedure

### 0. Read what exists and size the job

Read the stack (framework, and whether three, R3F, GSAP, or Motion already ship, since a library already in the bundle is free), the brand material on hand (logo as SVG or high-resolution PNG, palette, product photos or models, real copy), and who uses it on what devices.
Size the job as component polish, one signature moment, or a scene to fix.
A slow or ugly existing scene starts at step 3 with an audit against the references, then runs steps 4 and 5.

### 1. Find the idea in the subject

List 8 to 12 facts only this client has, then write "On this page, [one of them] becomes [a device]."
Swap in the nearest competitor's name, and if the sentence still works, go back to the list.
Bind the signature to real material, so the foundry's logo is poured as molten metal, the roaster's product turns under its own light, the dashboard's own numbers drive the motion.
Ask whether an image would work. If a still does the job, ship the still.
One loud moment per page, two or three scenes at most, with quiet sections between.
`references/ui-craft.md` has the full set of constructive moves and the font and theme procedures.

### 2. Pick the cheapest tier that lands it

| Tier | Reach for it when | Cost |
|---|---|---|
| 0. CSS and SVG | Depth tilt with `preserve-3d`, scroll reveals with `animation-timeline`, View Transitions, `feTurbulence` grain, `backdrop-filter` glass, clip-path reveals | 0KB |
| 1. Small libraries | Springs and gestures (Motion, React Spring), SVG drawing (Anime.js), Vanilla-Tilt, Zdog, a designer's asset in Rive (stateful) or Lottie (linear) | 5 to 30KB, measure |
| 2. Drop-in shader | An ambient folded gradient (shadergradient) on a React and R3F stack | three plus R3F, about 235KB gzipped if not already shipping, so load it in a lazy chunk |
| 3. Custom shader | Effects bound to a logo mask or wordmark, scroll or pointer reactive, or without three on a full-screen triangle | a few KB |
| 4. Three.js or R3F scene | Real objects, products, configurators, camera stories. Spline when a designer owns the scene, with GLB export as the way out | about 235KB gzipped before assets, in a lazy chunk |

Move up a tier only when a still of the higher tier clearly beats the lower one.
Record the tier and the reason as a `V` row.
A CSS 3D gotcha catches nearly everyone. Any grouping property on the `preserve-3d` element flattens every child layer. That means `overflow` other than visible (including `clip`), `opacity` below 1, `filter`, `mask`, `clip-path`, `mix-blend-mode`, and `isolation: isolate`.
Wrapping the Z-translated layers in a clipping element flattens them too. Clip each flat layer on its own wrapper, translate that wrapper as a unit, and keep the layers as direct children of the `preserve-3d` element.

### 3. Build with the invariants

Load the reference for what you are building. `references/3d-craft.md` for scenes, `references/effects.md` for shader signatures, `references/motion.md` for anything that moves, `references/ui-craft.md` for type, color, and components.
These invariants hold at every tier, and they are where generated code reliably breaks.

- **The first frame is readable.** Headline, sentence, and action are HTML on first paint. The canvas sits over a designed poster and fades in after its first rendered frame. No preloader.
- **One of each.** One canvas per page, one render loop, one scroll owner, one writer per property.
- **Nothing per frame that allocates or re-renders.** Refs and hoisted temporaries, never React state. Delta-based damping, `1 - Math.exp(-λ * dt)`.
- **Render only when something changes.** `frameloop="demand"` with `invalidate()` from tween `onUpdate`, and a pause off screen and in hidden tabs that keeps the animation's time. In R3F, `setFrameloop` resets `state.clock` to 0, so animate from your own accumulated time, never `clock.elapsedTime`.
- **Pixels are budgeted.** DPR capped at 2, at 1.5 on mobile, at 1 for soft gradients. Resolution uniforms in drawing-buffer pixels.
- **Degradation is designed, not bolted on.** Reduced motion shows a chosen still frame. No WebGL or a lost context shows the poster. Decorative canvases are `aria-hidden` with `pointer-events: none`, and meaning lives in DOM text.
- **Art direction replaces defaults.** Environment lighting with Neutral or AgX tone mapping (set as the last `<ToneMapping>` effect when a postprocessing composer is mounted, since the composer turns the renderer's off), fov 35 to 50, grounded objects, selective bloom, a brand palette, and component motion on the curves and durations in motion.md.

### 4. Make it seekable, then look

Drive every canvas from `scripts/seek-clock.js`, or for R3F the pattern in 3d-craft.md, so `?t=N` freezes the page at N seconds and sets `window.__ready`, and reduced motion freezes at the designed still.
Pass the clock a `whenReady` promise for every texture, font, or model the frame needs, or the frozen frame is captured without them. A frozen frame redraws itself on resize, and `clock.redraw()` covers anything else that clears the canvas.
CSS animations, transitions, and Web Animations are seeked by the capture script itself. GSAP timelines seek with `gsap.globalTimeline.pause().time(t)`, Lottie with `goToAndStop(t * 1000)`, and Rive and JS-driven springs need their own pause and seek. Scroll stories are captured at scroll positions instead.
Expose `window.__stats` with draw calls, triangles, and memory if the page has a renderer.

Then capture with Playwright installed in the project (`npm i -D playwright`).

```bash
node <skill>/scripts/capture.mjs http://localhost:3000 --t 0,1.2,4 --scroll 0.5,1 --out .evidence/shots
```

It shoots desktop 1440 at DPR 1 and mobile 390 at DPR 2, each seeked time and scroll position, reduced motion, and a no-WebGL launch, and writes a manifest with console errors, readiness, the WebGL renderer, and the stats.
A page with no seek clock still captures, but every shot waits out `--timeout` and reports NOT-READY, which is itself a finding.
If a Playwright or preview MCP is available instead, do the same steps through it.
**Read every image.** Check that the frame shows what you meant (the intended bronze can render teal), that the headline reads over the effect, that mobile is composed rather than cropped, that the reduced-motion and no-WebGL frames look designed, and that t=0 is not blank.
Use the artifact triage table in effects.md for black, white, or missing output.
When the user marks a region on a screenshot, map it to the code that draws it and change only that.

### 5. Measure and lint

- Compare `__stats` against the budgets in 3d-craft.md (about 100 draw calls, a hero model under 500KB, textures at 1024 on mobile, VRAM within 30 to 50MB on mobile).
- For scenes that mount and unmount, run the leak test (10 cycles, `renderer.info.memory` back to baseline).
- Headless WebGL runs on SwiftShader, a software renderer, so its frame rate means nothing. Report frame rate only from a real GPU, a headed browser on the user's machine or a device, and otherwise mark it `unverifiable`.
- Run the lint pass at the end of ui-craft.md, after your own critique.

### 6. Report with the V ledger

Write the ledger to the target repo's `.evidence/` in the shared format from `docs/specs/evidence-protocol.md`, one row per checkable claim.

| id | assertion | status | evidence | expiry | risk |
|---|---|---|---|---|---|
| V1 | Tier 3 custom shader, because the effect binds to the logo mask and three is not in the bundle | verified | package.json has no three, step 2 still comparison | stable | low |
| V2 | Hero reads on the first frame at 390 wide | verified | .evidence/shots/mobile-t0.png | on change | high |
| V3 | 1 draw call, 780x1752 buffer at mobile DPR 2 | verified | manifest.json mobile-t0 stats | on change | medium |
| V4 | Holds 60fps on a mid-range phone | unverifiable | headless is software rendered, no device run | | high |

Close with a short Before, After, Why table for what changed, and name the frames the user should open.
Never claim a screenshot or a measurement you did not take.

## Honest scope

Steps 0 to 3 and the lint need no tooling.
The captures need Playwright with its Chromium, or a browser MCP, and a page served over HTTP. Without them, the skill degrades to reading the code against the references and says so in every `V` row it could not capture.
Headless capture proves composition, readiness, degradation, and counts. It does not prove real-device frame rate, Safari rendering, or how the motion feels, and those stay flagged until someone checks them on hardware.
