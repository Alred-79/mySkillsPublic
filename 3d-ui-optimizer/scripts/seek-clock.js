// seek-clock.js: one time source for every animated visual on a page.
// ?t=N freezes the page at N seconds, renders that frame, and sets window.__ready,
// so scripts/capture.mjs can screenshot exact moments and compare them run to run.
// prefers-reduced-motion freezes at the designed still frame (stillAt) instead of going blank.
// The loop pauses while the tab is hidden or the element is off screen, and keeps its clock.
//
//   import { createSeekClock } from './seek-clock.js';
//   const clock = createSeekClock({
//     element: canvas, stillAt: 2.4,
//     whenReady: logoTexturePromise,          // __ready waits for the assets the frame needs
//     onFrame(t, dt) { draw(t); },
//   });
//   // After anything that clears or changes the drawing (a late asset, a manual resize), call clock.redraw().
//
// CSS and Web Animations are seeked by capture.mjs, not here. GSAP timelines seek with
// gsap.globalTimeline.pause().time(t), and Lottie or Rive need their own seek calls.

export function createSeekClock({ onFrame, element = null, stillAt = 0, whenReady = null, hitch = 0.25, onReady } = {}) {
  const params = new URLSearchParams(location.search);
  const seek = params.has('t') ? Number(params.get('t')) : null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const frozenAt = seek !== null && Number.isFinite(seek) ? seek : reduced ? stillAt : null;
  const assets = Promise.resolve(whenReady).catch(() => {});

  let assetsLoaded = false;
  let readyScheduled = false;
  const markReady = () => {
    if (readyScheduled || !assetsLoaded) return;
    readyScheduled = true;
    // One more frame so the drawn frame has been composited before a screenshot.
    requestAnimationFrame(() => {
      window.__ready = true;
      onReady?.();
    });
  };

  // A resize clears a canvas after it was drawn. Redraw on the next frame, after every
  // resize handler on the page has run, so a frozen frame is never left blank.
  let redrawQueued = false;
  const onResize = (redraw) => () => {
    if (redrawQueued) return;
    redrawQueued = true;
    requestAnimationFrame(() => {
      redrawQueued = false;
      redraw();
    });
  };
  const watchResize = (redraw) => {
    const handler = onResize(redraw);
    addEventListener('resize', handler);
    if (element && 'ResizeObserver' in window) new ResizeObserver(handler).observe(element);
  };

  if (frozenAt !== null) {
    const draw = () => onFrame(frozenAt, 0);
    draw();
    watchResize(draw);
    assets.then(() => {
      assetsLoaded = true;
      draw();
      markReady();
    });
    return { frozen: true, now: () => frozenAt, redraw: draw, stop() {} };
  }

  let elapsed = 0;
  let last = null;
  let raf = 0;
  let drawn = false;
  let visible = !document.hidden;
  let onScreen = true;
  let stopped = false;

  const tick = (ms) => {
    raf = 0;
    // The first frame always draws, so a canvas that starts off screen still has a frame and still signals ready.
    if (stopped || (drawn && (!visible || !onScreen))) {
      last = null;
      return;
    }
    // A gap longer than `hitch` (shader compile, tab switch) counts as one 60Hz frame,
    // so the animation never jumps. Slow devices keep real time instead of running in slow motion.
    const raw = last === null ? 0 : (ms - last) / 1000;
    const dt = raw > hitch ? 1 / 60 : raw;
    last = ms;
    elapsed += dt;
    onFrame(elapsed, dt);
    drawn = true;
    markReady();
    raf = requestAnimationFrame(tick);
  };

  const resume = () => {
    if (!raf && !stopped && (!drawn || (visible && onScreen))) raf = requestAnimationFrame(tick);
  };

  assets.then(() => {
    assetsLoaded = true;
    if (drawn) markReady();
  });
  document.addEventListener('visibilitychange', () => {
    visible = !document.hidden;
    resume();
  });
  if (element) {
    new IntersectionObserver(([entry]) => {
      onScreen = entry.isIntersecting;
      resume();
    }).observe(element);
  }
  watchResize(() => onFrame(elapsed, 0));
  resume();

  return {
    frozen: false,
    now: () => elapsed,
    redraw: () => onFrame(elapsed, 0),
    stop() {
      stopped = true;
      cancelAnimationFrame(raf);
    },
  };
}
