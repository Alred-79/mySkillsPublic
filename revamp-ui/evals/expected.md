# Expected: floor checks + dial-conditioned scoring

Scoring is three tiers (per docs/specs/revamp-ui.md and evidence-protocol.md), run with-skill vs a no-skill baseline arm, >= 3 reps, >= 2 model tiers. This is a creative skill: **never golden-output matching.** A redesign that diverges wildly from any reference is fine and must not be penalized for it. What is scored is (1) a binary constraint floor, (2) whether delivered intensity hit the dial the brief implies, and (3) diversity across reps.

## The three scoring tiers (shared across all cases)

**Tier 1 - constraint floor (automated, binary).** By construction this cannot punish creativity: any redesign, however divergent, should pass it.
- Renders with zero console errors.
- Original content, routes, and functionality preserved (the anti-greenfield check).
- Responsive at 2-3 widths.
- Contrast passes WCAG AA.
- LOCKED elements (from the contract) untouched: not removed, not restructured, SEO surface intact.

**Tier 2 - intensity vs contract (per-section, per-axis, 0-10).** The check a raw model never does. Scored against the dial the brief implies, **per section, not by average** - an average hides both the timid-hero undershoot and the everything-animates overshoot. Cross-section variance is its own metric. A miss triggers the directional correction verb (bolder if under, quieter if over).

**Tier 3 - diversity / anti-template.** Run the same brief 3-5x; extract font families, palette, and layout archetype from the generated code. Identical choices across reps = the skill collapsed into a template. Novelty and quality are SEPARATE axes that must both hold; Prompt Adherence keeps divergence-from-brief from winning (anti-Goodhart).

---

## Case 1: dated-dashboard-make-it-modern (fixture: slopdash)

The moderate-dial case, and the anti-greenfield control. The seeded slop and load-bearing list are in `fixtures/slopdash/README.md` (single source of truth, not copied here).

**Dial expectation:** a moderate-to-bold master, NOT maximal. A dashboard "made modern" wants polish and a real aesthetic decision, not a synthwave show. Pushing this to motion-9 is an overshoot; leaving it near-identical to the slop before-state is an undershoot (intensity decay).

**Floor (must hold):** every stat value and table row preserved; the `<select>` filter still works; all five routes still present; exactly one `h1` with the outline intact; title + meta preserved.

**Slop gate (must hold):** the mechanical detector ends with strictly FEWER banned-slop occurrences than the before-state. Concretely: the default `#6366f1` family is no longer the theme, emoji feature icons are gone, the `h1` is no longer gradient-clipped text, and a deliberate type system replaced the bare system-font stack.

**Inference (must hold):** the user said "go ahead", so the dials are inferred and stated in the contract; the skill does NOT stall on an `AskUserQuestion` round it was told to skip.

**RED baseline expectation:** the no-skill arm typically restyles surface colors but (a) keeps the same centered-hero + 3-card template, (b) often reaches for a *different* generic palette rather than a brief-fit one, (c) writes no contract and no LOCKED list, so it may quietly drop or rename the filter/routes, and (d) does not verify delivered intensity, so it lands wherever it happened to land. Merely mentioning "I modernized it" does not count; the specific floor and slop checks must pass.

## Case 2: maximal-immersive-landing (no fixture; bold brief)

The floor-side dial case: does the skill hold a bold brief bold instead of decaying to the safe middle?

**Dial expectation:** master ~9, motion 8-10, 3D at least tasteful-accent.

**Floor (the core check, must hold):** the delivered design meets the motion-8+ floor from `gates.md` - orchestrated load AND scroll-triggered choreography AND hover physics AND a signature motion moment, all present. A polished-but-static or single-fade-in result is an intensity-decay FAIL even though nothing is broken. This is the failure mode the floors exist to catch.

**Process gates (must hold):** a motion storyboard is produced before animation code (motion >= 6); the contract carries a first-class tiered degradation plan (a reduced-motion user gets a complete static equivalent, not an empty page); GSAP/Lenis usage matches the >= 6 allowlist; R3F appears only if 3D was opted in and is routed through 3d-web-experience, not hand-rolled.

**Overshoot guard (must hold):** even here, Phase 5 requires cross-section variance and readability. A page animated at 9 in every section is the exhausting-everything-animates failure and must NOT be scored as correct.

**Honesty (must hold):** if Playwright / preview / screenshot tooling is unavailable, the intensity scoring must state it came from structured self-review, never claim screenshots it did not take.

**RED baseline expectation:** the no-skill arm tends to produce *one* hero animation and call it immersive (misses the floor), rarely writes a degradation contract (a reduced-motion user gets a broken or empty page), and does not storyboard or verify per-section intensity.

## Case 3: calm-quiet-restraint (no fixture; calm brief)

The ceiling-side control, so floors and ceilings are both exercised across the suite. This case scores **restraint**, the mirror of case 2.

**Dial expectation:** master ~2, motion 1-3, strictest CWV posture.

**Ceiling (the core check, must hold):** the motion <= 3 ceiling from `gates.md` binds - NO scroll-triggered animation, no parallax, no autoplay, transitions <= ~200ms, emil frequency matrix strict. Sneaking spectacle back in (the user explicitly asked to remove it) is a ceiling FAIL.

**Library gate (must hold):** GSAP / Lenis / scroll-hijack libraries are NOT introduced (off the allowlist below motion 6); the low-motion end defers to emil-design-eng.

**Not-bland (must hold):** despite the calm dial, a real design decision is made - deliberate type, intentional hierarchy and spacing. Calm is not an excuse to do nothing; restraint is scored as quality. This is the anti-Goodhart guard so "minimize intensity" cannot be gamed by shipping a blank page.

**Overshoot correction (must hold):** Phase 5 flags any section delivering MORE than the calm dial for a "quieter" correction - the ceiling direction of intensity scoring, symmetric with case 2's "bolder".

**RED baseline expectation:** the no-skill arm often keeps some of the loud patterns the user complained about, or over-applies a generic "modern" look with motion the brief explicitly rejected, and does not record a low dial to correct against.

---

## Dial-conditioned delta (the cross-case check)

The three cases together are the intensity-delta test the spec calls for: the same skill, given a maximal brief (case 2) and a calm brief (case 3), must deliver measurably different intensity, each scored against its own contract. A skill that produces similar intensity for both has failed the core promise regardless of how either looks in isolation. The moderate case (1) sits between and additionally guards the anti-greenfield floor on a real before-state.
