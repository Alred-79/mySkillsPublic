# Motion for components, pages, GSAP, and 3D

Load this when anything moves.
Component rules come from emil-design-eng, page-scale numbers from taste-skill's award-site study, and the GSAP rules from GSAP 3.15 source and the official gsap-skills, checked 2026-10-24.
For GSAP API detail, route to the gsap-skills.

## Contents

- Whether to animate at all
- Curves, durations, springs
- Component details
- Page-scale motion
- Reduced motion
- GSAP rules a model gets wrong
- Driving Three.js or R3F from GSAP
- Signature recipes

## Whether to animate at all

How often a user sees it decides, before taste does.

| Seen | Motion |
|---|---|
| 100+ times a day (command palette, shortcuts) | None, ever |
| Tens of times a day (hover, list navigation) | Remove it, or cut it hard |
| Occasionally (modal, drawer, toast) | Standard |
| Rarely or first time (onboarding, a success moment) | Room for delight |

Never animate anything triggered from the keyboard.
Decorative motion is fine on a hero and wrong on a functional chart in a banking app.

## Curves, durations, springs

| Use | Curve | Duration |
|---|---|---|
| UI enter or exit | `cubic-bezier(0.23, 1, 0.32, 1)` | press 100 to 160ms, tooltip 125 to 200ms, dropdown 150 to 250ms, modal or drawer 200 to 500ms |
| Reveal at 800ms or more | `cubic-bezier(0.16, 1, 0.3, 1)` | 700 to 900ms |
| Moving across the screen | `cubic-bezier(0.77, 0, 0.175, 1)` | 400 to 600ms |
| Drawer | `cubic-bezier(0.32, 0.72, 0, 1)` | 300 to 500ms |
| Hover or color | `ease` | 150 to 200ms |
| Constant motion, scroll-linked | `linear` | locked to the source |

- UI animation stays under 300ms, so a 180ms dropdown beats a 400ms one.
- Exits take 60 to 75 percent of the entrance time.
- Never ease-in on UI. Ease-in is only for things leaving for good.
- No overshoot curves (y outside -0.1 to 1.1) and no bounce or elastic, except on drag release and small playful elements.
- Springs default to `{ type: 'spring', duration: 0.5, bounce: 0.2 }`, with bounce 0.1 to 0.3. Convert between libraries with the damping ratio ζ = c / (2√(k·m)). React Spring's 170/26 is about critical, and a 400/17 spring is visibly bouncy at ζ ≈ 0.42.
- Anything that can be re-triggered must be interruptible. Springs keep velocity, CSS transitions retarget, keyframes restart from zero. So use transitions or springs, and an Escape mid-expand reverses from where it is.
- Decorative pointer-follow, including a 3D tilt or camera parallax, uses a spring of stiffness 100 and damping 10 on `pointer * 0.1`, or GSAP `quickTo` at 0.6 to 1s `power3`.

## Component details

- Press is `:active { transform: scale(0.97) }` (0.95 to 0.98) over 100 to 160ms.
- Never enter from `scale(0)`. Start at 0.95 or more with opacity 0.
- Popovers grow from their trigger (`transform-origin` at the trigger, for Radix `--radix-popover-content-transform-origin`). Modals stay centered.
- A crossfade that looks like two objects is hidden with `blur(2px)` during the swap. Blur stays under 8px and is gone once settled.
- `@starting-style` instead of a mounted flag in an effect.
- `translateY(100%)` moves by the element's own height. Prefer it to pixel values.
- Once one tooltip is open, the next open instantly (`[data-instant] { transition-duration: 0ms }`).
- Stagger list items 30 to 80ms and never block interaction during the stagger.
- Gate hover effects behind `@media (hover: hover) and (pointer: fine)`. Do not lift every card on hover.
- Gestures dismiss when velocity exceeds 0.11 px/ms regardless of distance, add friction past a boundary instead of a hard stop, capture the pointer while dragging, and ignore a second finger once a drag starts.
- Set the transform on the moving element. A CSS variable on a parent restyles every child.
- Framer Motion's `x` and `y` props run on the main thread. A full `transform` string, CSS animations, and the Web Animations API stay smooth while the page is busy.
- Animate only transform, opacity, and clip-path. Layout changes go through Flip or View Transitions.
- clip-path recipes. Reveal with `inset(0 0 100% 0)` to `inset(0)`. Hold-to-confirm runs 2s linear while pressed and 200ms ease-out on release. A comparison slider drives `inset(0 50% 0 0)` from the drag position.
- Review output as a `| Before | After | Why |` table.

## Page-scale motion

- The load sequence settles within 1.2s, moves 4 elements or fewer, and has no preloader or gate. The headline is readable on the first frame.
- Reveals fire once when the element is 85 to 90 percent down the screen, rise 12 to 32px, and run 700 to 900ms. Picture openings run 1.1 to 1.3s.
- Staggers run 80 to 110ms for lines, 50 to 90ms for list items, and 20 to 40ms for characters on headings of 1 to 3 words, 4 steps at most.
- Scroll-linked motion is linear and locked to the scrollbar. Parallax travel stays under 8 percent, scale between 0.94 and 1.15.
- Two or three scenes per page, each held for 1 to 4 screens, with a quiet section between them. One loud moment per page.
- Native scroll only. Never capture the wheel. Lenis at lerp 0.1 to 0.14 is acceptable, and off for touch and reduced motion.
- Dimmed items stay at 40 percent or more. Page-to-page View Transitions run 480ms or less.
- The 0KB tier comes first. CSS `animation-timeline: view()` and `scroll()` for reveals and progress, `document.startViewTransition` for page and state transitions, `@starting-style` for entries.

## Reduced motion

Reduced motion is a designed finished state, not a kill switch.
The `0.01ms !important` reset breaks scroll scenes that rely on a finished state and can leave content invisible.

- Drop travel, scale, parallax, pinning, scrub, camera flights, and autoplay. Keep opacity and color changes at 300ms or less.
- Nothing is hidden. Hidden starting states live under `@media (prefers-reduced-motion: no-preference)` plus an `html.js` class, so a failed script also leaves content visible.
- 3D shows the designed still frame (seek-clock's `stillAt`).
- In GSAP, `duration: reduce ? 0 : 1` does nothing for scrubbed timelines, because their progress follows scroll. Build a separate `gsap.matchMedia()` branch for `(prefers-reduced-motion: reduce)` with no pins, no scrub, and fades only. `gsap.matchMediaRefresh()` supports an in-app motion toggle.

## GSAP rules a model gets wrong

**React.** `useGSAP` with `scope`, and `contextSafe` for handlers. Register plugins at module top. A `gsap.matchMedia()` created inside `useGSAP` joins its context and reverts on unmount, so never nest `gsap.context` inside it. Scope cleanup this way instead of `ScrollTrigger.getAll().forEach(kill)`.

**Refresh order.** React runs child effects before parents, so a parent's pin is created after its children's triggers and they measure wrong. After mount, after Suspense resolves, and after `document.fonts.ready`, call `ScrollTrigger.sort()` then `ScrollTrigger.refresh()`. Auto-refresh only happens on DOMContentLoaded, load, resize, and visibilitychange, so lazy images need their own refresh in `onload`.

**Pins.** A pin whose parent is `display: flex` silently gets `pinSpacing: false`, so the next section slides under it. Wrap it in a block element or set `pinSpacing` explicitly. Animate the pin's children, not the pin. `anticipatePin: 1` stops the jump on fast scroll. Use `pinnedContainer` for triggers inside a pinned element. One pin per chapter, never nested.

**Scrub.** Durations inside a scrubbed timeline are shares of the scroll distance, not seconds. Holds are empty tweens, `tl.to({}, { duration: 0.5 })`. `snap: { snapTo: 'labelsDirectional', duration: { min: 0.2, max: 0.6 } }`. Use function values with `invalidateOnRefresh: true` for anything sized from the viewport. ScrollTrigger goes on the top-level timeline only.

**Rendering.** `from()` with ScrollTrigger renders immediately, so stacked `from()` tweens on one property need `immediateRender: false` after the first. Hide elements with `visibility: hidden` in CSS and reveal with `autoAlpha` to avoid a flash. Tweens defer their first render to the end of the tick, so measuring or rendering a WebGL frame right after creating one sees old values. Use `gsap.set`, `lazy: false`, or `tween.progress(0)`.

**Mobile.** `ignoreMobileResize` is already on for touch devices. `ScrollTrigger.normalizeScroll(true)` is the real fix for iOS pin jitter and address-bar resize.

**Performance.** No blanket `will-change`. `force3D: 'auto'` already promotes during tweens, and ScrollSmoother's own source notes `will-change` performed worse on iOS. Reserve it for layers that move constantly. `quickTo` re-targets one property on any object with easing. `quickSetter` has no easing and is fastest, for values you already smoothed. A cursor is a quickSetter dot plus a quickTo ring at 0.5s.

**Clocks.** Lag smoothing treats a frame gap over 500ms as 33ms, which is right for intros. When GSAP must match an outside clock (Lenis, video, audio, a render loop), use `gsap.ticker.lagSmoothing(0)`. Lenis wiring is `lenis.on('scroll', ScrollTrigger.update); gsap.ticker.add((t) => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0)`. One scroll owner only, so never Lenis and drei ScrollControls together.

**License.** GSAP 3.15 including SplitText, ScrollSmoother, MorphSVG, and the other former Club plugins is free for commercial use under GreenSock's standard no-charge license, which is not an open source license. Install from public npm. Never generate an `.npmrc` pointing at the old private registry.

## Driving Three.js or R3F from GSAP

- Tween numbers on refs, never React state. `mesh.position`, `mesh.rotation` in radians, `uniforms.uProgress` as `{ value }`, `material.opacity` after setting `transparent = true`, and color through its `r`, `g`, `b` toward a precomputed `THREE.Color`.
- Derived updates go in the tween's `onUpdate`, never in `scrollTrigger.onUpdate`, because with numeric scrub the tween keeps catching up after the scroll stops. That means `camera.lookAt()`, `camera.updateProjectionMatrix()` when tweening fov, `controls.update()`, and `invalidate()` under `frameloop="demand"`.
- One property, one writer. One master scrubbed timeline per camera path with `ease: 'none'` and labels per beat. Disable OrbitControls during a scroll-driven flight, or animate a rig the controls do not own.
- One render loop. Vanilla three renders from `gsap.ticker.add(() => renderer.render(scene, camera))` or only from `onUpdate` for a static scene. R3F picks up ref mutations in its own loop.
- A fixed canvas behind DOM sections that provide the scroll length, with `{ trigger: storyRef, start: 'top top', end: '+=400%', scrub: 1 }`.
- `useGSAP` works inside `<Canvas>` children, but `scope` only scopes selector strings, so three targets are refs.
- Start intros only after assets load and shaders compile (`renderer.compileAsync` or a warm-up frame), or the compile hitch eats the first beat.
- Pointer parallax is `gsap.quickTo(group.rotation, 'y', { duration: 0.8, ease: 'power3' })` fed by `gsap.utils.mapRange(0, innerWidth, -0.25, 0.25)`.

## Signature recipes

**SplitText headline.** `SplitText.create(h, { type: 'lines', mask: 'lines', autoSplit: true, onSplit: (s) => gsap.from(s.lines, { yPercent: 100, duration: 1, ease: 'expo.out', stagger: 0.1 }) })`. Return the tween from `onSplit` so re-splits clean up. Words run 0.6 to 0.8s at stagger 0.03 to 0.06. Characters only on strings of about 30 or fewer, 0.4 to 0.6s at stagger 0.015 to 0.03, total spread 0.6s or less, with `font-kerning: none`. Keep `aria: 'auto'`, trigger at `start: 'top 80%'` with `once: true`, and avoid `text-wrap: balance` on split text.

**Flip, card to detail.** `Flip.getState(els, { props: 'borderRadius,backgroundColor' })` in the event handler before the state change, shared `data-flip-id`, then `Flip.from(state, { duration: 0.7, ease: 'power3.inOut', absolute: true, nested: true })` with entering items from scale 0.95 over 0.35s and leaving items out over 0.25s. Grid filters stagger 0.02 to 0.04.

**Scroll-scrubbed sequence.** Pin a 100vh section for about `+=100%` per beat at `scrub: 0.6` to `1`. An image sequence tweens `{ frame: 0 }` to `n - 1` with `snap: 'frame'` and `ease: 'none'`, drawing to a canvas in `onUpdate`.

**Horizontal scroll.** The official gsap-scrolltrigger skill's example is broken (a `Max.max` typo, pixels into `xPercent`, `Math.max(0, negative)` returning 0, and no scrub). Use this.

```js
gsap.to(track, {
  x: () => -(track.scrollWidth - innerWidth),
  ease: 'none',
  scrollTrigger: { trigger: wrap, pin: true, scrub: 1, end: () => '+=' + (track.scrollWidth - innerWidth), invalidateOnRefresh: true },
});
```

Nested triggers inside the track use `containerAnimation`.
