# gates.md - dial gates, slop list, renderer ladder

Loaded on demand at build (Phase 4) and verify (Phase 5) time, so SKILL.md stays terse.
Read the row for each contracted dial value and honor its floor, ceiling, and allowlist.

## Contents

- Motion dial gates (floors + ceilings + library allowlist)
- Density dial gates
- 3D opt-in gates
- Master dial rollup
- The slop list (what the detector keys on)
- Renderer-detection ladder (Phase 5 screenshots)
- Per-section intensity scoring rubric

---

## Motion dial gates

Both directions. The floor is a minimum the build must reach; the ceiling is a maximum it must not exceed. Floors exist because an unfloored brief drifts to the safe middle; ceilings exist because an uncapped one overshoots.

| Motion | Floor (at minimum, or it undershot) | Ceiling (must not exceed, or it overshot) | Library allowlist |
|---|---|---|---|
| 1-3 (calm) | Instant, legible state changes; focus-visible; considered hover affordances | NO scroll-triggered animation; transitions <= 200ms; no parallax; no autoplay; emil frequency matrix strict | CSS transitions only. No GSAP, no Lenis, no scroll libraries. |
| 4-5 (moderate) | Entrance transitions on key elements; smooth <= 300ms state changes; at least one intentional micro-interaction | No scroll-hijacking; no long-running looping animation; motion stays supportive, not the subject | CSS + small helpers (Motion One / Framer-style). GSAP allowed only for a single contained moment. |
| 6-7 (lively) | Scroll-triggered reveals on major sections; orchestrated (staggered) load; hover physics on interactive elements | No more than one simultaneous hero-scale effect competing for attention; respects reduced-motion with a real static fallback | GSAP + Lenis unlock. ScrollTrigger allowed. |
| 8-10 (show) | Orchestrated page load AND scroll-driven choreography AND hover physics AND at least one signature motion moment, all present | Cross-section variance must exist (not every section at max); page must not become unreadable or nauseating; 60fps target | GSAP + Lenis + scroll choreography. R3F only if 3D opted in. |

The motion >= 6 storyboard checkpoint (SKILL.md Phase 3) is mandatory before any animation code at these levels.

## Density dial gates

| Density | Floor | Ceiling |
|---|---|---|
| Low (airy) | Generous whitespace; one clear focal point per view; restrained element count | Must not become sparse-to-the-point-of-empty; content still scannable |
| Mid | Balanced rhythm; clear grouping | Neither cramped nor cavernous |
| High (dense) | Information-rich; efficient use of space; tight but legible grid | Must not cross into cramped/unscannable; hit-targets and line-length still hold |

A dense brief that ships airy has undershot; an airy brief that ships cramped has overshot. Gate both.

## 3D opt-in gates

| 3D level | What is allowed | Required routing |
|---|---|---|
| None (default) | CSS depth only (shadow, layering, subtle transform). No WebGL. | none |
| Tasteful accent | One contained depth moment. Prefer CSS/SVG; lightweight R3F only if it clearly earns the weight. | 3d-web-experience + r3f/three-best-practices |
| Core experience | 3D is a primary surface. | 3d-web-experience + r3f-best-practices + three-best-practices REQUIRED; do not hand-roll |

If 3D is opted in but the routed skills are unavailable, drop to a CSS-depth accent and state the downgrade. Unguided Three.js is worse than a good CSS accent.

## Master dial rollup

The master dial sets the defaults the sub-dials inherit unless the user diverged (Phase 1). Approximate mapping from the interview scenes to internal values:

| Scene | Master | Default motion | Default density | Perf budget posture |
|---|---|---|---|---|
| A - calm, instant | ~2 | 1-3 | low-mid | strictest CWV; ship near-static |
| B - polished, subtle | ~4 | 4-5 | mid | strict CWV |
| C - rich, reactive | ~7 | 6-7 | mid-high | relaxed but bounded CWV |
| D - immersive, a show | ~9 | 8-10 | any | loosest CWV, still a hard ceiling |

Perf budget scales inversely with the dials, but every tier keeps a hard CWV ceiling. Record the concrete LCP/CLS/INP targets in the contract.

---

## The slop list (detector keys on these)

The Phase 5 mechanical detector counts occurrences of these named defaults. Ship gate: the redesign must never contain MORE of them than the original page did. Each ships with the concrete alternative to reach for instead.

| Slop pattern | Why it reads as generic | Reach for instead |
|---|---|---|
| Centered hero + 3 feature cards + big gradient CTA | The canonical AI-generated landing template | A layout that follows this product's actual content shape |
| Default indigo/violet (`#6366f1` and neighbors) | The unmodified framework accent everyone ships | A palette derived from the brand or the chosen aesthetic family |
| Unmodified system-font stack as the type system | Signals "no type decision was made" | A deliberate type pairing with real hierarchy |
| Emoji as feature/section icons | Placeholder-grade; inconsistent rendering | A consistent icon set or bespoke marks |
| Evenly-spaced everything, no rhythm | Flat, monotonous, no emphasis | A spacing scale with intentional rhythm and focal contrast |
| Generic glassmorphism SaaS card grid | The 2021-era default look | Surface treatment that fits the family, used with restraint |
| Gratuitous gradient text on headings | Decorative default standing in for hierarchy | Weight, size, and spacing to build hierarchy |
| `box-shadow` on everything, uniform elevation | No real depth model | An intentional elevation system, sparingly applied |
| Hardcoded color/spacing magic numbers | Bypasses the token system; unmaintainable | Tokens from the Phase 4 token layer |
| Placeholder copy left in ("Lorem", "Your headline here") | Unfinished | Real content from the existing site (Phase 0) |

At high spectacle dials some of these (a bold gradient, a glass surface) may be *explicitly* wanted; the contract's banned list records which are banned and which are sanctioned for this brief, so the detector only counts the banned ones.

---

## Renderer-detection ladder (Phase 5 screenshots)

Try in order; use the first that works; record which rung you landed on so the report states its evidence honestly.

1. **Playwright MCP** (`browser_navigate` + `browser_take_screenshot`) - full control, can settle animations first. Preferred.
2. **Preview MCP** (`preview_start` + `preview_screenshot`) - good for a running dev server.
3. **Headless Chrome via a bundled/available script** - if the repo provides one.
4. **Structured self-review (fallback)** - no capture available. Read the built code and reason about delivered intensity per section. This is weaker evidence; the report MUST say the scores came from self-review, not screenshots.

**Headless trap handling (rungs 1-3).** Scroll-triggered and load-orchestrated animations render blank or half-drawn in a naive capture. Before shooting: scroll the page programmatically to fire scroll triggers, wait for load orchestration to complete, and/or force animation end-states. A blank capture of a rich section is a tooling artifact; scoring it as timid would misdirect a correction.

**CWV.** Measure against the contract budget where the tooling supports it (Playwright traces, Lighthouse if available). Where it does not, reason from the code (bundle weight, blocking resources, layout-shift risk) and mark the figure as an estimate, not a measurement.

---

## Per-section intensity scoring rubric

For each major section, score delivered intensity 0-10 on the axes the contract set (motion, density, and overall spectacle), then compare to the contracted dial.

- **On target** (within ~1 of the dial): pass.
- **Below target** (>= 2 under): undershoot -> trigger the "bolder" correction on that section.
- **Above target** (>= 2 over): overshoot -> trigger the "quieter" correction on that section.
- **Cross-section variance**: its own metric. Near-zero variance at a high dial = the everything-animates failure (exhausting); it needs quiet passages. Wild variance with a dead hero = the timid-hero failure. Choreography is the distribution, not the mean.

One correction per iteration so the effect is attributable; re-score after each; hard cap 5 iterations. Accessibility and CWV checks run every iteration regardless of the intensity scores.
