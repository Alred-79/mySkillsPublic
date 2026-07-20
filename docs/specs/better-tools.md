# Spec: better-tools

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md), chains [adversarial-verify.md](adversarial-verify.md)

## Purpose

Scan a whole app and recommend genuinely better tools — replace hand-rolled code with
libraries, swap a library for a better one, consolidate overlapping deps, modernize
deprecated/abandoned deps, swap dev-tooling (bundler / test-runner / linter / package
manager), suggest framework-level moves — **very wide, very far reach, multi-language**.

**The guardrails ARE the product.** A frontier LLM emits recommendations freely; what it
skips — every time — is the verification loop. So the skill's value is not the taste
("this lib is nicer," which the model already has) but the discipline that makes a
recommendation trustworthy. The delta this skill encodes is that discipline.

## Market position (researched + fact-checked 2026-07)

The target — a wide, far-reach, multi-language, repo-grounded, guardrailed, portable
recommender — is **unoccupied**. What exists: agent skills that are narrow (Nesbitt's
`managing-dependencies` vets what you propose but explicitly does NOT recommend
replacements; dependency-updater skills only bump versions; single-framework upgrade
skills); and SaaS/CLI that are wide-ish but not recommenders (Copilot App Modernization =
.NET/Java/C++ upgrades + Azure; Renovate/Dependabot = version bumps + a finite curated
`replacements.json`; deps.dev / OpenSSF Scorecard / Socket / ecosyste.ms = health signals,
no "switch to X"; OpenRewrite/Moderne = deterministic JVM recipes for known migrations;
ThoughtWorks Radar / StackShare = human opinion). The skill's reach STARTS where
Renovate's curated list ends, and can hand confirmed swaps to Renovate/OpenRewrite for the
deterministic apply.

## Why the guardrails must exist (empirical backbone — all fact-checked to primary sources)

- **Package hallucination**: USENIX Security 2025 ("We Have a Package for You!", 576k
  samples, 16 LLMs) — ~19.7% of recommended packages don't exist (5.2% commercial vs
  21.7% open models); 205,474 unique invented names. Frontier models improve but don't
  close it: arXiv 2605.17062 (2026) — 4.62%–6.10% across 5 frontier models, 127 names
  invented identically by all five (of which **53 remain registrable** after existing
  registry defenses — cite the 53, the actionable-threat count, not just the 127).
- **Recurrence enables the attack**: 43% of hallucinated names reappeared in ALL of 10
  re-queries — so "ask again to check" fails; this is the slopsquatting surface.
- **Staleness**: ICSE 2025 ("LLMs Meet Library Evolution", arXiv 2406.09834) — high
  deprecated-API-usage rates, larger models often no better; training cutoffs lag the
  ecosystem (the moment.js-after-EOL pattern; a raw model still recommends Snyk Advisor,
  whose standalone site sunset early 2026, migration completed by Feb 2026 per Snyk). The
  specific 25–38% figure must be confirmed against the paper PDF before it ships as a
  quoted number (the abstract-level sources didn't confirm it) — until then, "high rates".
- **Do NOT cite** the "OpenSSF Q2 2024 / 68% deprecated" stat — the research traced it to
  a marketing page with no OpenSSF primary source. Citation-hygiene rule below.

## Files

```
better-tools/
  SKILL.md                    # inventory → candidate generation → guardrail gauntlet → ranked proposal
  references/guardrails.md    # the 6 gates + the live source each grounds on
  references/registries.md    # per-language existence + health API endpoints (npm/PyPI/crates/pkg.go.dev/Maven; deps.dev, OpenSSF Scorecard, ecosyste.ms, Socket)
  evals/                      # colocated evals (layout per evidence-protocol.md)
```

**Citation-hygiene rule (skill-wide)**: every maintenance/health/adoption claim shown to
the user cites the live source it came from with an access date; the skill never asserts a
tool's status from model memory (that memory is the staleness bug). If a live check can't
be run, the recommendation is marked `unverified` and demoted — never presented as fact.

## Flow

**Phase 0 — Whole-app inventory.** Languages, package manifests + lockfiles, dev-tooling
(bundler/test/lint/format/CI/package manager), frameworks, and — critically — what the app
actually does and where (call-site scan, not just the manifest). Establishes the real
surface a recommendation would touch.

**Phase 1 — Candidate generation (wide, far reach).** Across the whole ecosystem, per
language: hand-rolled code that a mature library does better/safer; libraries with a
clearly better successor; overlapping deps to consolidate; deprecated/abandoned/EOL deps
to replace; dev-tooling swaps (e.g. legacy bundler→modern, heavy test-runner→lighter,
multi-tool→unified); framework-level moves where justified. Candidates are hypotheses —
untrusted until they pass the gauntlet.

**Phase 2 — The guardrail gauntlet (the product).** Each candidate must pass, in order;
failures are dropped or demoted, never shown as confident:

1. **Existence — suppress-on-unverifiable, NOT demote.** The package name is confirmed
   against the live registry (npm / PyPI / crates.io / pkg.go.dev / Maven Central — each
   has a distinct "does-not-exist" signal: 404 vs empty version list vs `numFound:0` —
   handle all) before it is ever shown. Kills hallucination / slopsquatting; the single
   highest-value gate. **If the registry is unreachable, the skill emits NO package-name
   recommendations for that ecosystem and says so — it never falls back to model memory
   and never renders an existence-unverified name, even demoted.** (Demotion is for
   gates 2/6 on a *real* package with stale health data; an unverifiable *name* is
   suppressed outright — a demoted-but-visible hallucination is still a supply-chain leak.)
2. **Freshness / health** — reject or flag abandoned/archived/EOL/single-maintainer/
   stale-release candidates via deps.dev (+ OpenSSF Scorecard), ecosyste.ms (last release,
   archived flag, dependents, bus factor), Socket (behavioral supply-chain risk).
3. **Stdlib-and-existing-deps-first** — before recommending anything new, check whether the
   language stdlib or an already-present dependency already does it (Nesbitt's core
   observation; "You-Don't-Need-X"-style enumerable checks). The best recommendation is
   often "delete a dep," not "add one."
4. **Repo-benefit grounding** — read the actual call-sites the change would touch; only
   recommend where the repo genuinely benefits. No generic "X > Y" without evidence from
   this codebase.
5. **Migration-cost quantification** — count affected call-sites, list breaking changes,
   estimate effort. Never present a swap as free.
6. **Anti-hype** — down-weight trendy-but-unproven; require adoption/maintenance evidence
   (Scorecard activity, dependents count); cross-check against a "hold"-style signal.

**Phase 3 — Ranked proposal (never auto-apply, with a volume floor).** Output: a
prioritized list, each item = the change, the grounded evidence (existence + health,
**carrying its receipt** — the observed response value, e.g. "last release 2019-03-14",
not just a URL + date, so it's re-derivable and can't be a ghost citation), the repo
benefit, the migration cost, and a confidence. Ranked by benefit ÷ migration-cost, with a
**benefit-threshold floor and a top-N cap**: anything below the floor is dropped (not just
ranked lower) with an "N more below threshold — ask to see them" affordance, so wide
generation never becomes 50-item alarm fatigue.

**Never-auto-apply is airtight**: the skill's only output artifact is a human-readable
proposal. It never writes a tool config (`renovate.json`, `rewrite.yml`), never invokes an
apply tool, and never emits a runnable migration command *as its action* — it may *quote*
the exact Renovate/OpenRewrite recipe in the proposal text for a human to run. Handing off
means quoting the recipe, not triggering it.

Closer: `REQUIRED: adversarial-verify` on the recommendation packet — each recommendation
is a `T` assertion carrying a **verification recipe** (the exact registry/health command to
re-run); the verifier's registry/existence sub-route executes it and diffs the observed
value against the claimed one. This chain is the skill's spine, not optional — it is the
only true backstop against a fabricated-but-plausible citation.

## Suite integration

Recommendations are evidence-protocol assertions (prefix `T`); each carries its live-source
citation as `evidence` and an `expiry` (health data goes stale). `unverified` candidates
use the protocol's `unverifiable` status — a finding, never a silent pass. adversarial-verify
consumes the packet directly; its "factual" routing (independent registry/health re-check
against today) is exactly the right verifier lens. Chains code-audit / productionize when a
recommended swap has security or operational implications.

## Evals & testing plan

Artifacts in `evals/`; shared rules in [evidence-protocol.md](evidence-protocol.md).
- **Fixture**: a polyglot repo with real opportunities (hand-rolled CSV parse a library
  does better; a deprecated dep with a live successor; two overlapping deps; a heavy
  dev-tool with a lighter swap the repo would benefit from) AND poisoned bait: a
  plausible-but-nonexistent package name, an EOL/abandoned package, a trendy-but-immature
  package, and a case where the stdlib already suffices.
- **Hallucination/EOL rejection (pass^k, the flagship gate)**: the skill must reject 100%
  of nonexistent and EOL bait every run — a recommender that surfaces a hallucinated
  package even 1-in-3 runs is a supply-chain hazard, not a skill. **Two layers**: a
  recorded registry snapshot for the deterministic CI grade (evidence-protocol's ≥3-rep
  determinism), PLUS a periodic live smoke test asserting the skill actually issues the
  network call (guards against snapshot-only breakage). The nonexistent bait uses a
  **guaranteed-permanently-invalid name** (violating each registry's naming rules, or a
  sentinel pointed at a mock endpoint returning 404) so no future squatter can register it
  and flip the eval.
- **Grounding (deterministic + judged)**: every surfaced recommendation cites a live
  source with a date; stdlib-first bait produces "you don't need a dep"; the immature-tool
  bait is demoted by the anti-hype gate; migration cost is present and call-site-grounded.
- **Benefit precision**: recommendations only where the fixture genuinely benefits (FP rate
  on the clean/decoy deps).
- **No-auto-apply (airtight)**: even on a Renovate-ready fixture, the skill produces no
  `renovate.json`/`rewrite.yml`, invokes no apply tool, and runs no install/migration
  command — output is a human-readable proposal that may quote the recipe. Also asserts a
  volume floor: on a fixture full of marginal opportunities, output stays bounded and every
  surfaced item clears the benefit floor.
- **Per-check obsolescence** (delta-only): prune any guardrail sub-check the baseline
  already performs — but the hallucination/EOL gates will not prune (baselines fail them,
  per the cited rates), which is the point.
- **RED baseline**: an unguarded agent asked "recommend better libraries" — expected
  failures per the research: invents packages, recommends an EOL tool, ignores the stdlib,
  gives generic X>Y with no call-site grounding, undersells migration cost. GREEN: the
  gauntlet catches all bait. REFACTOR.

## Out of scope

Auto-installing or auto-migrating (Renovate/OpenRewrite own the deterministic apply; the
skill produces the cited proposal and can hand off by *quoting* the recipe). Security-vuln
scanning of current deps (code-audit / Socket own that; this skill recommends *better*
tools, and routes security implications to those). Version-bump-only maintenance
(dependency-updater skills own it).

**Boundary with code-audit's existence/health check** (both run this class of check):
code-audit audits the *current* dependency tree for hallucinated/unmaintained packages;
better-tools applies existence/health gates only to its *proposed replacements*. When both
are in play, better-tools consumes code-audit's findings for the current tree and does not
re-scan existing deps — an overlap turned into a pipeline, not duplicate work.
