# Spec: revamp-ui

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

Complete user-centric UI revamp of an **existing** site/app, conditioned on the user's
elicited tolerance for spectacle vs simplicity. The closed preference loop - interview →
contracted numeric dials → floors *and* ceilings → build → **screenshot-scored delivered
intensity vs the contract** - is unduplicated on the market (researched 2026-07 across
three waves; closest competitor educlopez/ui-craft has knobs and ceilings but no
interview, no floors, and verification that never checks whether the design *hit* the
knob values).

## Files

```
revamp-ui/
  SKILL.md              # inventory → interview → contract → variants → build → verify
  gates.md              # dial-value → floors/ceilings/allowlists (loaded at verify time)
  contract-template.md  # DESIGN-CONTRACT.md template
  evals/                # colocated evals (layout per evidence-protocol.md):
    evals.json          #   fixtures/ = slop pages + before-state bank + dial-conditioned briefs;
    fixtures/  judge/   #   judge/ = blind-pairwise rubric incl. Creative Distinction
```

Routes through installed skills where present (hybrid rule): frontend-design/impeccable
for execution, emil-design-eng governs low motion dials, 3d-web-experience +
r3f/three-best-practices REQUIRED at 3D opt-in. Contract altitude per Anthropic guidance:
terse (~hundreds of tokens), specific bans + concrete alternatives; heavy tables load
on demand.

## Flow

**Phase 0 - Inventory.** Read the codebase: stack, tokens, components, pages, what works.
Revamp ≠ greenfield: map existing components to revamped successors.

**Phase 1 - Interview.** ONE round max (AskUserQuestion, ≤5 questions, concrete
scenarios, never abstract numbers); **"go ahead" grants permission to infer everything**
(fall back to a taste-skill-style inference table + the user's taste profile).
- Master dial: A "calm, instant, nothing moves" → D "the site is a show" (→ 1–10).
- 3D: no / tasteful accent / core experience.
- Motion + density sub-dials: "same as overall" default + divergence options.
- **Owner-vs-audience tension check:** who are the users? If owner taste conflicts with
  audience reality, surface the conflict explicitly; record the resolution in the contract.
- References: "1–2 sites you love" → check VoltAgent/awesome-design-md for pre-extracted
  DESIGN.md first; else study-style 5-dimension extraction (with the ethics layer: no
  cloning paid templates or a designer's signature work).

**Phase 2 - DESIGN-CONTRACT.md** (persisted; every phase re-reads; user-editable; updates
the cross-project taste profile). Contents: numeric dials, aesthetic family, locked
tokens, one signature element, **LOCKED elements** (brand colors, working components, IA
- and **SEO surface: URLs, heading semantics, meta, structured data**), named banned
slop defaults, perf budget scaling inversely with dials, and the **degradation contract**
(tiered experience: full / reduced-motion / static / low-end mobile - first-class, not
bolted on).

**Phase 3 - Direction variants.** Parallel subagents emit 2–3 throwaway static HTML
mockups differentiated on a named axis (superdesign technique). User picks by looking.
Refresh / reskin / rebuild scope stated out loud. Then the **preview checkpoint**: a
markdown block of every committed choice before build costs are paid. At motion ≥ 6:
**motion storyboard checkpoint** - what moves, when, triggered by what, why - approved
before animation code.

**Phase 4 - Build.** Strict order: tokens → typography → spacing → components → motion.
Constraint gates from `gates.md` with **floors and ceilings**: motion ≥ 7 floor =
orchestrated load + scroll reveals + hover physics *at minimum* (floors prevent intensity
decay); motion ≤ 3 ceiling = no scroll animation, ≤ 200ms transitions, emil frequency
matrix strict. Library allowlist: GSAP/Lenis unlock at motion ≥ 6; R3F only with 3D
opt-in. Density gates both directions.

**Phase 5 - Two-layer verify.**
- Mechanical gates (deterministic scripts): contrast, hardcoded-value lint, slop-pattern
  detector. Ship gate: never more detector findings than the original had.
- **Intensity scoring:** Playwright screenshots (desktop + mobile; renderer-detection
  ladder with an honesty notice when degraded). Handle the headless trap: settle scroll
  animations / force end-states, or motion-rich sections screenshot blank. Score
  delivered intensity **per section, per axis, 0–10 vs the contract** - choreography, not
  just averages: catch the timid hero AND the exhausting everything-animates page;
  cross-section variance is its own metric.
- Score miss auto-triggers the directional correction verb (bolder/quieter), one fix per
  iteration, hard cap 5 iterations. A11y always (reduced-motion, contrast, keyboard);
  CWV per the contract's budget. Optional closer: adversarial-verify.

## Evals & testing plan

Eval architecture (artifacts in `evals/`; shared rules in
[evidence-protocol.md](evidence-protocol.md)) - creativity-preserving, three tiers,
**never golden-output matching**:
1. **Constraint floor (automated, binary)**: renders, zero console errors, original
   content/routes/functionality preserved, responsive at 2–3 widths, contrast passes,
   locked elements untouched. Any redesign however divergent should pass - the floor
   cannot punish creativity by construction.
2. **Blind pairwise screenshot judging** (the anthropics/skills PR #210 protocol -
   75% win rate, p=0.006 from ~30 comparisons): bank of 15+ before-states; revamp vs
   baseline; Puppeteer screenshots; anonymized A/B to a judge scoring Prompt Adherence,
   Aesthetic Fit, Visual Polish, UX, and **Creative Distinction** (divergence is a
   scored criterion, not a penalty); order-swapped; binomial test on decisive wins.
   Judge fit-to-brief, never similarity-to-reference.
3. **Diversity metric (anti-template check)**: same brief 3–5×; extract font families,
   palette, layout archetype from generated code; identical choices across reps = the
   skill collapsed into a template. Anti-Goodhart: novelty and quality stay SEPARATE
   axes that must both hold; Prompt Adherence keeps divergence-from-brief losing.
Plus dial-conditioned cases: a motion-9 and a motion-2 brief scored against their
contracts - the intensity-delta check is part of the eval.

TDD cycle - RED: baseline on the slop fixture with a "maximal immersive" brief -
expected failures: timid output (intensity decay), slop defaults, no fallbacks,
greenfield rewrite, SEO surface broken. GREEN/REFACTOR: floors hold, contract persists,
per-section scores drive corrections, locked elements untouched.
