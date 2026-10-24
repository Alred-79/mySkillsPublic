// seek-clock.js: one time source for every animated visual on a page.
// ?t=N freezes the page at N seconds, renders that one frame, and sets window.__ready,
// so scripts/capture.mjs can screenshot exact moments and compare them run to run.
// prefers-reduced-motion freezes at the designed still frame (stillAt) instead of going blank.
// The loop pauses while the tab is hidden or the element is off screen, and keeps its clock.
//
//   import { createSeekClock } from './seek-clock.js';
//   const clock = createSeekClock({ element: canvas, stillAt: 2.4, onFrame(t, dt) { draw(t); } });

export function createSeekClock({ onFrame, element = null, stillAt = 0, maxDelta = 1 / 30, onReady } = {}) {
  const params = new URLSearchParams(location.search);
  const seek = params.has('t') ? Number(params.get('t')) : null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const frozenAt = seek !== null && Number.isFinite(seek) ? seek : reduced ? stillAt : null;

  let readyScheduled = false;
  const markReady = () => {
    if (readyScheduled) return;
    readyScheduled = true;
    // One more frame so the drawn frame has been composited before a screenshot.
    requestAnimationFrame(() => {
      window.__ready = true;
      onReady?.();
    });
  };

  if (frozenAt !== null) {
    onFrame(frozenAt, 0);
    markReady();
    return { frozen: true, now: () => frozenAt, stop() {} };
  }

  let elapsed = 0;
  let last = null;
  let raf = 0;
  let visible = !document.hidden;
  let onScreen = true;
  let stopped = false;

  const tick = (ms) => {
    raf = 0;
    if (stopped || !visible || !onScreen) {
      last = null;
      return;
    }
    // Clamp the delta so a long hitch (shader compile, tab switch) never jumps the animation.
    const dt = last === null ? 0 : Math.min((ms - last) / 1000, maxDelta);
    last = ms;
    elapsed += dt;
    onFrame(elapsed, dt);
    markReady();
    raf = requestAnimationFrame(tick);
  };

  const resume = () => {
    if (!raf && !stopped && visible && onScreen) raf = requestAnimationFrame(tick);
  };

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
  resume();

  return {
    frozen: false,
    now: () => elapsed,
    stop() {
      stopped = true;
      cancelAnimationFrame(raf);
    },
  };
}
