#!/usr/bin/env node
// capture.mjs: look at a visual before claiming it works.
// Screenshots a page at seeked times (?t=N, see seek-clock.js), at scroll positions, under
// reduced motion, and with WebGL disabled, at desktop and mobile sizes. Reports console errors,
// whether the page signalled window.__ready, the WebGL renderer, and window.__stats if exposed.
//
//   node capture.mjs <url> [--t 0,2,4] [--scroll 0,0.5,1] [--out shots] [--timeout 10000]
//                          [--settle 800] [--no-degraded]
//
// Playwright is resolved from the current working directory (npm i -D playwright there).
// Headless WebGL runs on SwiftShader, a software renderer, so frame rate here means nothing.
// Draw calls, triangles and memory from window.__stats are the numbers that transfer.

import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const argv = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i === -1 ? fallback : argv[i + 1];
};
const url = argv[0] && !argv[0].startsWith('--') ? argv[0] : null;
if (!url) {
  console.error('usage: node capture.mjs <url> [--t 0,2,4] [--scroll 0,0.5,1] [--out shots] [--no-degraded]');
  process.exit(1);
}
const list = (s) => (s ? s.split(',').map(Number).filter(Number.isFinite) : []);
const times = list(opt('t'));
const scrolls = list(opt('scroll'));
const out = resolve(opt('out', 'shots'));
const timeout = Number(opt('timeout', 10000));
const settle = Number(opt('settle', 800));
const degraded = !argv.includes('--no-degraded');

let chromium;
try {
  ({ chromium } = createRequire(pathToFileURL(join(process.cwd(), 'noop.js')))('playwright'));
} catch {
  console.error('playwright not found from this directory. Run: npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}

const VIEWPORTS = {
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
};
const GL_ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const NO_GL_ARGS = ['--disable-webgl', '--disable-3d-apis'];

const withT = (u, t) => {
  const x = new URL(u);
  x.searchParams.set('t', String(t));
  return x.href;
};

mkdirSync(out, { recursive: true });
const shots = [];

async function shoot(browser, { name, vp, target, reducedMotion = 'no-preference', scrollFraction = null }) {
  const ctx = await browser.newContext({ ...VIEWPORTS[vp], reducedMotion });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(target, { waitUntil: 'load', timeout });
  const ready = await page
    .waitForFunction(() => window.__ready === true, null, { timeout })
    .then(() => true, () => false);
  if (scrollFraction !== null) {
    await page.evaluate(async (f) => {
      const max = document.documentElement.scrollHeight - innerHeight;
      // Step a frame at a time so scroll-linked triggers see every intermediate position.
      for (let i = 1; i <= 20; i++) {
        window.scrollTo(0, (max * f * i) / 20);
        await new Promise((r) => requestAnimationFrame(r));
      }
    }, scrollFraction);
  }
  // Scrubbed timelines keep catching up after the scroll stops, so let them settle.
  if (!ready || scrollFraction !== null) await page.waitForTimeout(settle);
  const info = await page.evaluate(() => {
    const c = document.createElement('canvas');
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    let renderer = null;
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      renderer = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    }
    return { webgl: !!gl, renderer, stats: window.__stats ?? null };
  });
  const file = join(out, `${name}.png`);
  // animations: 'disabled' jumps CSS transitions to their end state, so a canvas fade-in is never caught half drawn.
  await page.screenshot({ path: file, animations: 'disabled' });
  await ctx.close();
  const row = { name, file, ready, errors, ...info };
  shots.push(row);
  return row;
}

const gl = await chromium.launch({ args: GL_ARGS });
for (const vp of Object.keys(VIEWPORTS)) {
  if (times.length) {
    for (const t of times) await shoot(gl, { name: `${vp}-t${t}`, vp, target: withT(url, t) });
  } else {
    await shoot(gl, { name: `${vp}-live`, vp, target: url });
  }
  for (const s of scrolls) await shoot(gl, { name: `${vp}-scroll${s}`, vp, target: url, scrollFraction: s });
  if (degraded) await shoot(gl, { name: `${vp}-reduced-motion`, vp, target: url, reducedMotion: 'reduce' });
}
await gl.close();

if (degraded) {
  const noGl = await chromium.launch({ args: NO_GL_ARGS });
  await shoot(noGl, { name: 'desktop-no-webgl', vp: 'desktop', target: url });
  await noGl.close();
}

writeFileSync(join(out, 'manifest.json'), JSON.stringify({ url, capturedAt: new Date().toISOString(), shots }, null, 2));
for (const s of shots) {
  const flags = [s.ready ? 'ready' : 'NOT-READY', s.webgl ? `gl:${s.renderer}` : 'no-gl', s.errors.length ? `${s.errors.length} errors` : 'clean'];
  console.log(`${s.name.padEnd(24)} ${flags.join('  ')}${s.stats ? '  stats ' + JSON.stringify(s.stats) : ''}`);
  for (const e of s.errors) console.log(`    error: ${e}`);
}
console.log(`\n${shots.length} shots + manifest.json in ${out}`);
console.log('Headless WebGL is software rendered. Read frame cost from stats, not from how smooth it felt here.');
