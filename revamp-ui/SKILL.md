---
name: revamp-ui
description: Complete user-centric UI revamp of an EXISTING site or app, conditioned on the user's elicited tolerance for spectacle vs simplicity. Runs a one-round interview to set numeric dials, writes a persisted DESIGN-CONTRACT, builds against floors AND ceilings, then screenshot-scores the delivered intensity back against the contract. Use this whenever the user asks to "redesign this UI", "make this look better", "revamp our landing page", "modernize this interface", says "the design feels dated / generic / like every other AI site", or wants it "more immersive" or "calmer / simpler". Reach for it for any restyle, reskin, visual overhaul, or "make it feel modern/premium/alive" of an interface that already exists, even when the user does not say the word "redesign". Not for greenfield UI from scratch (no existing code to inventory) and not for backend or non-UI work.
---

# Revamp UI

Take an interface that already exists and revamp it to a level of spectacle the user actually asked for, then prove you hit that level.

The whole skill is a closed preference loop: interview to set the dials, write them into a contract, build against the contract's floors and ceilings, then screenshot the result and score the delivered intensity back against the same dials. Skip any link and it degrades into a generic restyle, which is the thing the user's own model already does for free.

## The delta-only rule (read this first)

Encode only what a frontier model won't already do when asked to "make this look better". Two moves it skips on its own, and the entire value of the skill:

1. **It doesn't ask how much.** Asked to modernize a UI, a raw model picks one intensity (usually a safe, mid, slightly-generic one) and runs. It never elicits whether this user wants "calm and instant, nothing moves" or "the site is a show", and it never records that choice so later phases can honor it.
2. **It doesn't check whether it hit the number.** A model renders the redesign and calls it done. It never screenshots its own output and scores the delivered intensity against a target, so a hero it *meant* to be dramatic ships timid and nobody notices.

Everything below serves those two gaps: elicit the dial, contract it, and verify the delivered design against it. If you catch yourself writing generic design advice a competent model already gives unprompted (use whitespace, pick a nice font, add hover states), delete it. The value is the dial and the verification, not the styling tips.

## Anti-greenfield stance

Revamp is not a rewrite. The user has working code, real content, live URLs, and a brand. Your job is to change how it looks and feels while keeping what works working. A redesign that quietly drops a working component, breaks a route, or resets the brand palette to a fresh default has failed even if the new pixels are beautiful. Phase 0 exists to make that failure mode impossible, and the contract's LOCKED list (Phase 2) enforces it through every later phase.

## Routing to the design skills (hybrid rule)

This skill owns the loop: interview, contract, direction pick, ordered build, intensity verification. It does not re-teach visual craft. Route execution to the installed design skills where they are present, and fall back to your own judgment where they are not:

- **frontend-design** and **impeccable** drive the actual look, typography, and polish during Phase 4 build and the Phase 3 variants. They are the execution engine; this skill is the conductor.
- **emil-design-eng** governs the low-motion end. At motion dial <= 3, defer to its frequency matrix and restraint before adding any animation.
- **3d-web-experience** plus **r3f-best-practices** / **three-best-practices** are REQUIRED once the user opts into 3D. Do not hand-roll WebGL. If 3D is opted in and these are unavailable, say so and drop 3D to a tasteful CSS-depth accent rather than shipping unguided Three.js.
- **adversarial-verify** is an optional closer on the finished DESIGN-CONTRACT ledger (it reads `D` rows directly, per evidence-protocol.md).

Invoke a routed skill via the Skill tool when it is listed as available; otherwise proceed with the guidance here. The contract stays terse on purpose (a few hundred tokens): specific bans plus concrete alternatives, with the heavy dial tables loaded on demand from `gates.md`. Altitude discipline keeps the contract re-readable at the top of every phase.

## Phase 0 - Inventory (map what exists)

Read the codebase before touching it. Record:

- **Stack and tooling**: framework, CSS approach (Tailwind? CSS modules? styled-components?), existing design tokens or theme file, component library if any, build setup.
- **Component and page map**: enumerate the real components and pages. For each meaningful one, note what it does and whether it works. This becomes the migration map: every existing component gets an explicit revamped successor or an explicit "kept as-is".
- **What already works**: interactions, flows, and content that are load-bearing and should survive untouched.
- **The SEO surface**: URLs, heading semantics (the `h1`/`h2` outline), meta tags, structured data. This is invisible in a screenshot and trivial to destroy in a restyle, so name it now.

Write a `D` row for the inventory summary in the target repo's evidence ledger (`.evidence/`, per evidence-protocol.md). The inventory is what makes this a revamp and not a greenfield rewrite: you cannot preserve what you never mapped.

## Phase 1 - Interview (one round, concrete scenarios)

One round only, via `AskUserQuestion`, five questions maximum. Ask in terms of concrete experiences, never abstract numbers: a user knows whether they want "the page feels like a quiet document" or "the page reacts to me as I scroll", but "pick a motion value 1-10" means nothing to them. You translate their scenario answers into the numbers internally.

**"Go ahead" grants full permission to infer.** If the user says "go ahead", "just do it", "you pick", or similar, skip the interview and infer every dial from: the repo's current aesthetic, the product's domain and audience, and the user's stored taste profile (`~/.claude/.../taste-profile.md` or repo `.design/`, per evidence-protocol.md). State the inferred dials out loud in the contract so the user can correct them. Do not stall a user who already delegated.

Elicit these:

- **Master dial - spectacle vs simplicity.** The anchor everything else defaults from. Offer the poles as scenes: A = "calm, instant, nothing moves, gets out of the way" through D = "immersive, the site is a show, motion and depth everywhere". Map the answer to 1-10 internally (A~2, B~4, C~7, D~9), so `gates.md` can gate on it.
- **3D opt-in.** Three explicit levels: none / a tasteful accent (a subtle depth moment) / a core 3D experience. Default none. 3D is opt-in because it carries real performance and accessibility cost and is the single biggest driver of build complexity.
- **Motion and density sub-dials.** Offer "same as the overall feel" as the default for each, plus divergence options (for example "bold layout but calm motion", or "dense and information-rich" vs "airy and spacious"). Most users want coherence with the master dial; the divergence options exist for the ones who don't, so you are not forcing a single global slider onto a design that wants a quiet hero and a lively features section.
- **Owner-vs-audience tension check.** Ask who the actual users are. If the owner's stated taste conflicts with the audience's reality (a maximal, animation-heavy brief for a screen-reader-heavy accessibility tool; a playful spectacle for an enterprise compliance dashboard), surface the conflict explicitly and record how it was resolved in the contract. You are the one person in the loop who represents the end user, so name the tension rather than silently building what the owner asked.
- **References - "1 to 2 sites you love".** If given, check `VoltAgent/awesome-design-md` or a shipped `DESIGN.md` for a pre-extracted profile first. Otherwise do a study-style extraction across a few dimensions (type, color, space, motion, composition). Ethics layer: extract the *principles*, never clone a paid template or a named designer's signature work. Judge fit-to-brief, not similarity-to-reference.

## Phase 2 - The DESIGN-CONTRACT

Write `DESIGN-CONTRACT.md` into the target repo from `contract-template.md`. It is persisted, re-read at the top of every later phase, and user-editable (if the user hand-edits a dial, that edit wins). On completion it updates the cross-project taste profile so the next revamp starts from this user's known preferences.

The contract records:

- **Numeric dials**: master, 3D, motion, density (the internal 1-10 values from Phase 1), each as a `D` assertion row.
- **Aesthetic family** and **one signature element**: the single memorable moment this design will be known for. One, not a list; a signature everywhere is a signature nowhere.
- **LOCKED elements** (the anti-greenfield contract): brand colors, working components that stay, the information architecture, and the SEO surface from Phase 0 (URLs, heading semantics, meta, structured data). Locked means later phases may restyle it but not remove or restructure it.
- **Named banned slop defaults**: name them and give the concrete alternative, do not just say "avoid generic". Defaults to ban unless the brief explicitly wants them: the centered-hero + three-feature-cards + big-gradient-button template, `#6366f1`-family default indigo/violet, unmodified default system-font stacks, emoji as feature icons, evenly-spaced everything with no rhythm, the generic SaaS glassmorphism card grid. See `gates.md` for the full slop list the detector keys on.
- **Perf budget**, scaling inversely with the dials: a motion-9 / 3D-core design gets a looser budget than a motion-2 static one, but every tier still has a hard CWV ceiling. Record the target (LCP, CLS, INP) so Phase 5 can check it.
- **The degradation contract**: the tiered experience, treated as first-class, not bolted on. Define what full, reduced-motion (`prefers-reduced-motion`), static (no-JS), and low-end-mobile users each get. A spectacle that only exists at full tier and collapses to nothing for a reduced-motion user is a broken contract, not a graceful one.

## Phase 3 - Direction variants and checkpoints

Before paying full build cost, let the user pick a direction by looking at real pixels.

- **Parallel direction variants.** Dispatch subagents to emit 2 to 3 throwaway static HTML mockups (single file each, no build step), each committing hard to a *different named axis* so the choice is real and not three shades of the same idea (for example "editorial-restrained" vs "kinetic-maximal" vs "brutalist-utilitarian"). State the scope out loud: refresh (reskin tokens only) vs reskin (components too) vs rebuild (layout and structure). The user picks by seeing, which is faster and truer than picking from a description.
- **Preview checkpoint.** After the pick, restate every committed choice (chosen direction, dials, signature element, locked list, scope) as a short markdown block and get a go-ahead. This is the last cheap moment to change course before build cost is spent.
- **Motion storyboard checkpoint** (only when motion dial >= 6). Before writing any animation code, describe the choreography in prose: what moves, when, triggered by what, and why it earns the attention. Get approval on the storyboard first. Motion is expensive to build and easy to overdo, so agreeing on the plan before the code is what prevents an exhausting everything-animates result.

## Phase 4 - Build (ordered, with floors and ceilings)

Build in strict dependency order so each layer rests on a settled one: **tokens -> typography -> spacing -> components -> motion**. Motion is last because animating an unsettled layout means redoing the motion.

Load `gates.md` now and apply the constraint gate for each dial value. The gates run **both directions**, and this is the core mechanic:

- **Floors prevent intensity decay.** A dial value sets a *minimum*, not just a cap. At motion >= 7 the floor is orchestrated load + scroll-triggered reveals + hover physics *at minimum*: shipping less than that is a miss even though nothing is technically broken. Floors exist because "modernize this" without a floor drifts toward the safe middle every time; the floor is what holds a bold brief bold.
- **Ceilings prevent overshoot.** At motion <= 3 the ceiling is no scroll animation, transitions <= 200ms, emil frequency matrix strict. A calm brief that sneaks in parallax has overshot its dial just as surely as a bold brief that stayed timid undershot.
- **Library allowlist by dial.** GSAP / Lenis unlock at motion >= 6. R3F unlocks only with the 3D opt-in. Below those thresholds the heavier libraries are off the menu, because reaching for a scroll-hijack library on a calm brief is how a quiet design ends up loud.
- **Density gates both directions** too: a dense brief must not ship airy, an airy brief must not ship cramped.

The exact floor / ceiling / allowlist rows per dial value live in `gates.md`; read it at build time and honor the row for each dial.

## Phase 5 - Two-layer verify

Two independent layers. The first is mechanical and deterministic; the second scores taste against the contract.

**Layer 1 - mechanical slop gates.** Deterministic checks you run by reading the built code, or with a script if the repo adds one: contrast (WCAG AA), a hardcoded-value lint (colors and spacing should come from tokens, not magic numbers), and the slop-pattern detector from `gates.md`. **Ship gate: the redesign may never have more detector findings than the original page had.** You are here to reduce slop, so ending with more of it than you started with is an automatic fail regardless of how the result looks.

**Layer 2 - intensity scoring against the contract.** This is the check the raw model never does.

- **Screenshot the delivered design** at desktop and mobile widths. Use Playwright or the preview tools if available; follow the renderer-detection ladder in `gates.md`. When the tooling is unavailable, degrade to a structured self-review (read the built code and reason about delivered intensity per section) and *say so in the report* - a self-review is weaker evidence than a screenshot and the user deserves to know which one they got. Never claim a screenshot you did not take.
- **Handle the headless-screenshot trap.** Scroll-triggered and load-orchestrated animations render as blank or half-drawn in a naive headless capture, which would score a rich section as empty. Before capturing, settle the animations: scroll the page programmatically, wait for load orchestration to finish, or force end-states. A blank screenshot is a tooling artifact, not a timid design, and scoring it as timid would send you correcting a section that was fine.
- **Score per section, per axis, 0 to 10, against the contract dial.** Not one global average: an average hides both failure modes. Choreography matters, so compute cross-section variance as its own metric. A page where every section screams at 9 is as wrong as a page where the hero whispers at 3 while the contract said 8. Catch the timid hero AND the exhausting everything-animates page.
- **A miss auto-triggers the directional correction verb.** Delivered below target -> go bolder on that section; above target -> go quieter. One fix per iteration so you can attribute the change, hard cap of 5 iterations. Re-score after each.
- **Accessibility always, regardless of dial**: `prefers-reduced-motion` honored, contrast passing, keyboard navigation intact. **CWV against the contract's budget.** Accessibility is never traded for spectacle; the degradation contract from Phase 2 is what lets a maximal design stay accessible.

Optional closer: chain **adversarial-verify** on the `D` ledger to have a blind verifier re-derive whether the delivered design actually meets each contracted dial.

## Honest scope

What works today, with no external tooling: the interview, the contract, the ordered build, the mechanical self-review, and the per-section intensity scoring by reasoning over the built code. The screenshot-and-CWV half of Phase 5 uses Playwright or the preview MCP tools *if they are available in the session*, and degrades to a structured self-review that names itself as such when they are not. The skill does not ship its own renderer, screenshot harness, or CWV measurement tool, and it never claims a captured screenshot or a measured Core Web Vital it did not actually produce. The slop detector and any screenshot-scoring harness a repo chooses to add are an optional hardening layer; the loop stands on the interview, the contract, and the honest self-review without them.
