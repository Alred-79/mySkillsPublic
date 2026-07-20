---
name: better-tools
description: Scan a whole app and recommend genuinely better libraries, tools, and dev-tooling - with every recommendation grounded in a live registry/health check, not model memory. Replaces hand-rolled code with mature libraries, swaps a library for a better successor, consolidates overlapping deps, modernizes deprecated/abandoned/EOL deps, and swaps dev-tooling (bundler, test-runner, linter, formatter, package manager). Multi-language, wide reach. Use this whenever the user asks "are there better libraries for this", "modernize our stack", "should we replace X", "what tools are we missing", "audit our dependencies for better options", "what's the modern way to do this now", or wants an outside-in look at what their project could swap in. Every proposal carries a re-runnable verification recipe and cites the observed value it was grounded on; the skill never writes a config or runs a migration - it proposes, a human applies.
---

# Better tools

Scan a whole app and recommend genuinely better tools: replace hand-rolled code with a library, swap a library for a better one, consolidate overlapping deps, retire deprecated/abandoned deps, swap dev-tooling. Wide reach, multi-language.

## The guardrails ARE the product (read this first)

A frontier model already has the taste. Ask it "what's a nicer HTTP client" and it answers instantly and often well. What it skips, every single time, is the verification loop. So the value of this skill is not the recommendation - it is the discipline that makes a recommendation trustworthy. **The delta this skill encodes is that discipline, not the opinion.**

That discipline exists because the unguarded behavior is measurably dangerous:

- **Models invent packages that don't exist.** USENIX Security 2025 ("We Have a Package for You!", 576k samples, 16 models) found ~19.7% of recommended packages are hallucinated (5.2% for commercial models, 21.7% for open ones), with 205,474 unique invented names. Frontier models shrink but do not close the gap: a 2026 study (arXiv 2605.17062) measured 4.62%-6.10% across five frontier models, with 127 names invented identically by all five - and **53 of those remain registrable** after existing registry defenses, so they are a live slopsquatting target, not a solved problem.
- **Asking again does not catch it.** 43% of hallucinated names reappeared in all 10 re-queries. The hallucination is stable, so "re-prompt to double-check" fails by design. The only real check is hitting the registry.
- **Model memory is stale by construction.** ICSE 2025 ("LLMs Meet Library Evolution", arXiv 2406.09834) found high deprecated-API-usage rates, and larger models are often no better. Training cutoffs lag the ecosystem: the model recommends the thing that was current when it was trained (moment.js after its EOL notice, a tool whose standalone site has since sunset). Its confidence about a package's health is the exact bug.

Read that as the mandate: **an unverified recommendation is worse than no recommendation, because it launders a guess as advice.** Every gate below turns a guess into evidence or drops it.

## What this skill does NOT do

- **It never applies anything.** No writing `renovate.json` or `rewrite.yml`, no invoking an apply tool, no running an install or migration command as its action. Its only output is a human-readable proposal. It may *quote* the exact Renovate/OpenRewrite recipe for a human to run - quoting the recipe is the hand-off; triggering it is not. See the airtight rule in Phase 3.
- **It does not scan the current tree for vulnerabilities.** That is code-audit and Socket. This skill applies its gates to the *proposed replacements*. If code-audit has already flagged the current deps, consume those findings; do not re-scan.
- **It does not do version-bump maintenance.** Renovate/Dependabot own "same package, newer version." This skill starts where the curated replacement list ends.

## Phase 0 - Whole-app inventory

You cannot recommend a replacement for code you have not read. Build the real surface first.

- **Languages and manifests.** Enumerate every package manifest and lockfile (`package.json` + lock, `pyproject.toml`/`requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`/`build.gradle`, and so on). Record the language of each subtree.
- **Dev-tooling.** Identify the bundler, test runner, linter, formatter, package manager, and CI. These are recommendation targets too, and often the highest-leverage ones.
- **Frameworks.** Note the framework(s) in play; framework-level moves are in scope but carry the highest migration cost, so they need the strongest grounding.
- **Call-site scan (the part models skip).** Do not stop at the manifest. Read what the app actually *does* and *where*: grep the call-sites a candidate change would touch. A dependency listed but imported in one file is a different proposition from one threaded through forty. This scan is what makes Phase 2 gate 4 (repo-benefit) real instead of generic.

Output of Phase 0: the concrete surface a recommendation would land on. Everything downstream cites it.

## Phase 1 - Candidate generation (wide, far reach)

Now generate hypotheses across the whole ecosystem, per language. Be wide here - this is the one phase where the model's breadth is an asset, because the gauntlet will kill anything that does not survive. Look for:

- **Hand-rolled code a mature library does better or safer** (a hand-written CSV/date/URL parser, a bespoke retry loop, an ad-hoc argument parser).
- **A library with a clearly better successor** (a maintained modern replacement for a legacy one).
- **Overlapping deps to consolidate** (two libraries doing the same job; keep one).
- **Deprecated / abandoned / EOL deps to replace** with a live successor.
- **Dev-tooling swaps** where the repo would benefit (legacy bundler to a modern one, a heavy test runner to a lighter one, several single-purpose tools to one unified tool).
- **Framework-level moves** where genuinely justified.

Treat every candidate as a hypothesis, untrusted, guilty until the gauntlet proves it. A candidate is not a recommendation. It becomes one only by surviving Phase 2 intact.

## Phase 2 - The guardrail gauntlet (the product)

Each candidate must pass these six gates **in order**. A failure drops or demotes the candidate; a failed candidate is never shown as confident advice. The gates and the live source each grounds on are in `references/guardrails.md`; the exact per-registry API endpoints and their distinct not-found signals are in `references/registries.md`. Read `references/registries.md` before running gate 1 or 2 so you issue the right call and read the right field.

**Gate 1 - Existence. Suppress-on-unverifiable, NOT demote.** Before a package name is ever shown, confirm it against the live registry (npm / PyPI / crates.io / pkg.go.dev / Maven Central). Each registry has a *distinct* does-not-exist signal - a 404, an empty version list, a `numFound: 0`, a non-200 - and you must handle the right one per registry (see `references/registries.md`). This is the single highest-value gate: it is the only thing standing between the model's ~19.7% hallucination rate and the user's lockfile.

The failure mode here is asymmetric, so the rule is asymmetric:

- If the name resolves, proceed to gate 2 carrying the observed response value.
- If the name does **not** resolve, **suppress it outright.** Do not demote it, do not show it with a caveat. A demoted-but-visible hallucination is still a supply-chain leak - the user can still copy it into a manifest.
- **If the registry itself is unreachable, emit NO package-name recommendations for that ecosystem, and say so.** Never fall back to model memory. Never render an existence-unverified name, even demoted. "I could not reach PyPI, so I am not recommending any Python packages this run" is the correct output; a plausible-but-unchecked name is not.

Demotion (below) is only ever for gates 2 and 6 acting on a package whose name already resolved - a *real* package with stale or thin health data. An unverifiable *name* is suppressed, full stop.

**Gate 2 - Freshness / health.** For a name that passed gate 1, check that it is actually alive. Reject or flag candidates that are archived, abandoned, EOL, single-maintainer, or long past their last release. Ground this on live health sources, never model memory: deps.dev and OpenSSF Scorecard (maintenance and security-practice signals), ecosyste.ms (last release, archived flag, dependents count, bus factor), Socket (behavioral supply-chain risk). Capture the observed value you keyed the decision on - "last release 2019-03-14", "archived: true" - because that value is the receipt Phase 3 carries and adversarial-verify re-checks.

**Gate 3 - Stdlib-and-existing-deps-first.** Before recommending anything new, check whether the language stdlib or a dependency already in the manifest does the job. The best recommendation is frequently "delete a dep" or "you don't need one," not "add one." This is the enumerable "You-Don't-Need-X" check: a hand-rolled deep-clone when the runtime now ships `structuredClone`, a date library when the stdlib date API covers the actual usage, a left-pad when the language has padding built in. A candidate that fails this gate converts into a *subtractive* recommendation, which is usually the better finding.

**Gate 4 - Repo-benefit grounding.** Go back to the call-sites from Phase 0 and read the actual code the change would touch. Recommend only where *this* repo genuinely benefits. No generic "X is better than Y" is allowed without evidence from this codebase - the benefit has to be visible at a real call-site. A candidate that is objectively nicer but touches code that does not exercise the difference is dropped.

**Gate 5 - Migration-cost quantification.** Never present a swap as free. Count the affected call-sites (you already have them), list the breaking changes, and estimate effort. The proposal ranks on benefit divided by this cost, so an unquantified cost makes the item unrankable.

**Gate 6 - Anti-hype.** Down-weight the trendy-but-unproven. Require adoption and maintenance evidence (Scorecard activity, dependents count, release cadence) before surfacing a young project, and cross-check against a "hold"-style signal. A package can be real (gate 1), maintained by its one enthusiastic author (gate 2 marginal), and still too immature to stake a migration on. This gate demotes it rather than dropping it, and the demotion is stated with its evidence.

## Phase 3 - Ranked proposal (never auto-apply, with a volume floor)

Emit a prioritized list. Each surviving item carries:

- **The change** - concretely, from what to what.
- **The grounded evidence, carrying its receipt.** Existence and health, expressed as the *observed value*, not just a URL and a date. "ecosyste.ms reports last release 2019-03-14, archived: true (fetched 2026-07-20)" is a receipt; "see ecosyste.ms" is a ghost citation waiting to happen. The receipt makes the claim re-derivable and is what the verifier diffs against.
- **The repo benefit** - the specific call-sites that improve, from gate 4.
- **The migration cost** - affected call-sites, breaking changes, effort, from gate 5.
- **A confidence.**

**Rank by benefit ÷ migration-cost.** Then apply a **benefit-threshold floor and a top-N cap**: anything below the floor is *dropped*, not merely ranked lower, with an affordance - "N more opportunities fell below the benefit threshold; ask to see them." Wide generation must never turn into a 50-item wall of alarm fatigue. A short list of high-confidence, high-benefit swaps is the product; an exhaustive dump is noise.

**Never-auto-apply is airtight.** The only artifact this skill produces is the human-readable proposal above. It does not write a tool config (`renovate.json`, `rewrite.yml`). It does not invoke an apply tool. It does not emit a runnable install/migration command *as its action*. It *may* quote the exact Renovate or OpenRewrite recipe inside the proposal text, clearly marked as "for you to run," so a human can hand a confirmed swap to the deterministic apply. Quoting the recipe is the hand-off. Triggering it is out of scope, always.

## Closing - chain adversarial-verify (the spine, not optional)

Emit each recommendation as a `T`-prefixed assertion row in the evidence ledger (`.evidence/` in the target repo, per evidence-protocol.md). Each row carries its live-source citation as `evidence`, an `expiry` (health data goes stale, so a re-check date is mandatory), and a **verification recipe**: the exact registry/health command to re-run.

Then chain **`REQUIRED (if available): adversarial-verify`** on the recommendation packet. This is the skill's spine, not a nicety. adversarial-verify's factual routing has a registry/existence sub-route built for exactly this: it executes each recipe independently and diffs the observed value against the value you claimed. That independent re-check is the only true backstop against a citation that is plausible but fabricated - a receipt no one re-derives is just a nicer-looking guess. If adversarial-verify is not installed, run the verification recipes yourself before presenting: re-hit each registry and health source and diff the observed value against what you claimed. The independent re-check is mandatory; the verifier skill is the preferred way to get it, not the only way.

A candidate that could not be checked (registry unreachable, health source down) is recorded with the protocol's `unverifiable` status. That is a finding, never a silent pass, and per gate 1 it means the *name* was suppressed, not shown.

Also chain **code-audit / productionize** when a recommended swap carries security or operational implications, and consume code-audit's existing-tree findings rather than re-scanning current deps.

## Honest scope

This is a scan-and-propose skill, and it works today: the gates run by the agent hitting live registries and health APIs with Bash and WebFetch, reading the fields documented in `references/registries.md`. There is no external tooling to install and none is assumed - the endpoints are public HTTP. The never-auto-apply rule is a hard constraint, not a default you can override: this skill proposes, and a human applies. Every health and existence claim it shows cites a live source with a fetch date, because the alternative - asserting a package's status from model memory - is the staleness bug this skill exists to defeat.
