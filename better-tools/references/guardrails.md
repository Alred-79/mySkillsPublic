# Guardrails: the six gates and what each grounds on

The gauntlet from SKILL.md Phase 2, in depth. Each gate below states the check, the live source it grounds on, and why an unguarded model fails it.
SKILL.md runs the gates in order; this file holds the reasoning and the anchors you recite to the user.
The exact API endpoints and their not-found signals live in `registries.md`; read that file before issuing a call.

## Contents

- [Citation-hygiene rule](#citation-hygiene-rule)
- [The empirical backbone](#the-empirical-backbone)
- [Gate 1 - Existence (suppress-on-unverifiable)](#gate-1---existence-suppress-on-unverifiable)
- [Gate 2 - Freshness / health](#gate-2---freshness--health)
- [Gate 3 - Stdlib-and-existing-deps-first](#gate-3---stdlib-and-existing-deps-first)
- [Gate 4 - Repo-benefit grounding](#gate-4---repo-benefit-grounding)
- [Gate 5 - Migration-cost quantification](#gate-5---migration-cost-quantification)
- [Gate 6 - Anti-hype](#gate-6---anti-hype)

---

## Citation-hygiene rule

Every health, maintenance, or adoption claim shown to the user cites a live source with an access date and the observed value it was read from. The skill never asserts a tool's status from model memory - that memory is the staleness bug the whole skill exists to defeat. If a live check cannot run, the claim is `unverifiable` (a finding, never a pass); an existence-unverifiable *name* is suppressed outright, not shown demoted. Same rule as `registries.md`, restated here because it governs every gate.

---

## The empirical backbone

Why the gates must exist, all traced to primary sources. Recite these when a user asks why a scan is worth the extra calls.

- **Package hallucination.** USENIX Security 2025, "We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs" (576,000 samples, 16 models): ~19.7% of recommended packages do not exist. Commercial models 5.2%, open models 21.7%. 205,474 unique invented names observed. This is the base rate gate 1 exists to intercept.
- **Frontier models shrink it but do not close it.** arXiv 2605.17062 (2026): 4.62%-6.10% hallucinated across five frontier models; 127 package names were invented *identically* by all five models, and **53 of those 127 remain registrable** after existing registry defenses. Cite the 53 - the actionable-threat count, the names a squatter could still register today - not just the 127. A better model is not a substitute for the check.
- **Re-querying does not catch it.** 43% of hallucinated names reappeared in all 10 re-queries. The hallucination is stable across samples, so "ask the model again" is not a verification. Only the registry is. This is the slopsquatting surface: a stable, predictable invented name is one a squatter can pre-register.
- **Staleness.** ICSE 2025, "LLMs Meet Library Evolution" (arXiv 2406.09834): high deprecated-API-usage rates in model output, and larger models are often no better. The mechanism is the training cutoff: the model recommends what was current when it was trained, not what is current now (the moment.js-after-EOL pattern; a raw model still recommending a tool whose standalone service has since sunset). Gate 2 exists because the model's confidence about health is precisely the unreliable part.
  - Note on the specific figure: the frequently-quoted "25-38% deprecated-usage" number is **not confirmed** against the paper's primary text at the time of writing. Say "high rates," not the number, until the PDF confirms it.
- **Do NOT cite the "OpenSSF Q2 2024 / 68% of dependencies deprecated" statistic.** It traces to a marketing page with no OpenSSF primary source. It is debunked; using it would itself be the ghost-citation failure this skill guards against.

---

## Gate 1 - Existence (suppress-on-unverifiable)

**Check.** Confirm the exact package name against its live registry before it is ever shown. Read the right not-found signal per registry (`registries.md`, "The four distinct not-found signals").

**Grounds on.** The registry itself: npm registry, PyPI JSON API, crates.io API, the Go module proxy (`@v/list`), Maven Central search (`numFound`). The registry is the source of record for existence; nothing else is.

**The rule is asymmetric because the failure is asymmetric.**
- Name resolves -> proceed to gate 2, carrying the observed response.
- Name does not resolve (clean 404 / `numFound:0` / etc.) -> **suppress outright.** Not demoted, not shown with a caveat. A demoted-but-visible hallucinated name is still a name the user can paste into a manifest, which is the whole attack.
- Registry unreachable (non-200 that is not a 404, rate-limit, timeout) -> **emit no package-name recommendations for that ecosystem this run, and say so.** Never fall back to model memory. "I could not reach crates.io, so no Rust package recommendations this run" is correct output.

**Why the model fails it.** It does not run the check at all - it emits the plausible name and moves on (the ~19.7% base rate above). This is the single highest-value gate; everything else is refinement.

**This gate never demotes.** Demotion is only for gates 2 and 6 acting on a name that already passed gate 1. Existence is binary and pre-display.

---

## Gate 2 - Freshness / health

**Check.** For a name that passed gate 1, establish that it is actually alive: not archived, abandoned, EOL, single-maintainer, or long past its last release. Reject the dead; flag the marginal.

**Grounds on** (all in `registries.md`):
- **deps.dev** - latest version and publish date, advisories, and the inline OpenSSF Scorecard link.
- **OpenSSF Scorecard** - the Maintained check and overall score; low Maintained is a strong abandonment signal.
- **ecosyste.ms** - `latest_release_published_at` (staleness), removal/deprecation `status`, `archived` flag, and dependents counts (adoption).
- **Socket** - behavioral supply-chain risk (install scripts, obfuscation, capability changes) the others do not model; skip and mark un-run if no API key.

**Capture the observed value** you decided on - "last release 2019-03-14", "archived: true", "Scorecard Maintained: 0". That value is the receipt Phase 3 carries and adversarial-verify diffs against. A decision with no captured value is not re-derivable.

**Why the model fails it.** Its health knowledge is frozen at the training cutoff (the staleness backbone above). It will confidently call a since-abandoned library "well-maintained" because it was, when the model was trained. This gate replaces that memory with a live read.

**Demotes, not suppresses:** a real package with stale/thin health data is shown demoted with its evidence, so the user can weigh it. (Contrast gate 1, where the *name* itself is unverifiable and gets suppressed.)

---

## Gate 3 - Stdlib-and-existing-deps-first

**Check.** Before recommending anything new, check whether the language standard library or a dependency already in the manifest already does the job. The best recommendation is often "delete a dep" or "you don't need one."

**Grounds on.** The repo's own manifest (already inventoried in Phase 0) and the language's standard library surface - the enumerable "You-Don't-Need-X" class of check. Examples: a hand-rolled deep-clone when the runtime now ships `structuredClone`; a date library when the stdlib date API covers the actual call-sites; a small utility dep whose one used function has a stdlib equivalent.

**Why the model fails it.** It reaches for a well-known third-party library by reflex (that is what its training data is full of) and under-weights the stdlib, especially recently-added stdlib features that post-date common training data. Nesbitt's core observation: the highest-value dependency change is frequently removal.

**Outcome.** A candidate that fails this gate does not vanish - it *converts* into a subtractive recommendation ("drop X, use the stdlib / the dep you already have"), which is usually the stronger finding.

---

## Gate 4 - Repo-benefit grounding

**Check.** Return to the call-sites from Phase 0 and read the actual code the change would touch. Recommend only where *this* repo genuinely benefits, with the benefit visible at a named call-site.

**Grounds on.** The repo itself - the call-site scan from Phase 0. This gate is the reason Phase 0 reads code and not just manifests.

**Why the model fails it.** It emits generic "X is better than Y" with no reference to whether the codebase exercises the difference. A library that is objectively nicer but touches code that never hits the improved path is not a benefit here; it is churn. No generic superiority claim passes without codebase evidence.

---

## Gate 5 - Migration-cost quantification

**Check.** Count the affected call-sites (you have them from Phase 0/gate 4), list the breaking changes, and estimate effort. Never present a swap as free.

**Grounds on.** The repo (call-site count) plus the candidate's own changelog / migration guide for breaking changes. Both are checkable, neither is model memory.

**Why the model fails it.** It undersells or omits migration cost, presenting a swap as a clean win. The proposal in Phase 3 ranks on benefit ÷ cost, so an unquantified cost makes the item unrankable and the ranking meaningless.

---

## Gate 6 - Anti-hype

**Check.** Down-weight the trendy-but-unproven. Require adoption and maintenance evidence before surfacing a young project, and cross-check against a "hold"-style caution signal.

**Grounds on.** OpenSSF Scorecard activity, ecosyste.ms dependents counts, and release cadence - the same live sources as gate 2, read here for adoption and durability rather than liveness. A "hold"-style radar signal (ThoughtWorks-style caution) is a cross-check, not a source of truth.

**Why the model fails it.** Its training data over-represents whatever was hyped in the window it was trained on, so it recommends the buzzy thing. A package can be real (gate 1), maintained by its one enthusiastic author (gate 2 marginal), and still far too immature to stake a migration on.

**Demotes, not suppresses:** an immature-but-real candidate is shown demoted with its adoption evidence stated, so the user sees both the appeal and the risk.
