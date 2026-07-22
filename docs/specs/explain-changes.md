# Spec: explain-changes

Status: approved design, skill + eval fixtures authored and hardened after a paired smoke trial (full benchmark run pending)
Depends on: [evidence-protocol.md](evidence-protocol.md)
Siblings: [adversarial-verify.md](adversarial-verify.md) (audits this skill's E-ledger), [microworld.md](microworld.md) (the deep-understanding counterpart, boundary drawn below)

## Purpose

Explain a code change at ship time so a human can trust it before it merges.
Read the real diff, ground every claim in a specific hunk or a real command output, scope the true blast radius across the repo, and produce a terse reviewer-facing brief that says what changed, what it touches, what to test, how to roll back, and what could not be verified.
Language-agnostic, one change at a time, at the moment of shipping.

## The delta-only rule

Encode ONLY what a frontier model will not produce on its own when asked "explain this change" or "write the PR description."
A raw model, and Claude Code's own built-in commit and PR drafting, will summarize the diff and restate the author's intent, and it does this for free.
What it does not do on its own, and what this skill encodes, is four things.

1. Ground each claim in the actual diff or a real run, instead of narrating remembered intent. The model that wrote the code is the worst-placed narrator of it, because it reports what it meant to do, and intent and code diverge exactly where the defect hides.
2. Scope the real blast radius by finding the true dependents across the repo, including the call sites the change does NOT affect, which is signal a reviewer cannot get from the diff alone.
3. Separate what was verified from what is a guess, and flag the unverifiable rather than smoothing it into a confident sentence.
4. Run the tests that exercise the change and report the real result, rather than promising the reviewer to test it.

Empirical backbone, researched 2026-07.
Frontier assistants already draft commit messages and PR bodies from the diff unprompted (Claude Code, Cursor one-click commit generation, Copilot `/explain` on the free tier), so the summarize-the-diff layer is commodity and adds nothing.
The purpose-built PR explainers people pay for (CodeRabbit as category leader, Qodo Merge and PR-Agent as the open-source option, Graphite, Greptile, Bito, Ellipsis) do produce walkthroughs, but the recurring, well-documented complaint is superficial, noisy, or occasionally wrong summaries, and none of them ground the explanation in a real test run from inside the coding agent.
Anthropic's own Opus 4.8 system card documents that the model glosses over failures in its own summaries a small but nonzero fraction of the time (verify the exact figure against the system card before quoting it), which is precisely the intent-parrot failure this skill counters.

## Market position (researched 2026-07)

The closest existing agent skill is understand-anything's `/understand-diff`, which reports what a PR changed plus affected components and risk, but it reads a pre-built static knowledge graph, has no runtime grounding, does not verify claims back against the diff, and ships inside a heavy eight-skill plugin that must build the graph first.
Neither obra/superpowers nor the official anthropics/skills ships a dedicated explain-a-change skill, so no default owns this niche, and not one skill in the surveyed set grounds a change explanation in a real execution.
Distinct value, the intersection nobody occupies: in-agent, at ship time, grounded strictly in the real diff and a real test run, scoped by true cross-file dependents, reviewer-altitude, and honest about the unverifiable.

## Boundary with microworld (the anti-duplication rule)

microworld and explain-changes share this repo's DNA, a claim is worth nothing unless it is tied to a real artifact, but they are different jobs and must not collide on triggering.

| | microworld | explain-changes |
|---|---|---|
| Moment | you want to learn code, before or after ship | the moment of shipping, before merge |
| Motion | pull, the learner chooses to go deep | push, the change is explained as it goes out |
| Output | a heavy, playable, browser learning artifact with a comprehension gate | a terse text brief for a reviewer |
| Depth | one surprising path, inhabited deeply | one change, scoped for a merge decision |
| Reach | Python-only, single-process, sandbox receipt | language-agnostic |

Rule of thumb written into both descriptions. If the user wants to inhabit and truly understand a path, that is microworld. If they want to explain and de-risk what was just shipped, that is this skill.

**The funnel (added 2026-07-22).** explain-changes is the first pass, microworld is the deep tier you escalate to for a playable run, and adversarial-verify audits either ledger. microworld's trigger surface was narrowed the same day to explicit deep-learning intent so the two do not collide on a bare "explain this diff" request; the review-and-ship phrasings live here. A paired smoke trial on 2026-07-22 showed a frontier baseline already caught the original marquee traps, so the checkout fixture was hardened (subtle overclaim plus transitive blast radius) to keep the eval a frontier task.

## Files

```
explain-changes/
  SKILL.md          # scope -> capture -> blast radius -> ground -> brief -> self-check
  evals/            # colocated evals (layout per evidence-protocol.md)
```

SKILL.md carries the whole payload here (the flow, the two mechanisms, the ledger, the boundary, the scope gate).
There is no reference catalog to load, because the delta is a disciplined procedure, not a body of domain facts. This is a deliberately lean skill.

## The two mechanisms (preserve these or the skill is theater)

**Grounding.** Every line in the brief is tied to a specific hunk (`file:line`) or a real command output. The commit message, the branch name, and the model's own recollection are claims to check, never sources to copy. A statement that cannot be tied to evidence is not stated as fact, it is flagged for the reviewer. This is the anti-parrot, anti-gloss mechanism, and it is the same discipline as microworld's every-number-from-a-trace and adversarial-verify's evidence-required.

**Reviewer altitude.** The brief answers only the questions a reviewer must resolve to decide whether to merge, and omits the ones the diff already answers. The per-file list of what changed is free and already on the PR page, so it is left out. The blast radius, the test result, and the rollback are what the reviewer cannot easily see, so they are surfaced. A brief that drifts into a whole-repo tour is the noise failure the paid tools are criticized for, and it is a scored failure here.

## Flow

**Phase 0 - Scope the change and the audience (one light round; "go ahead" = infer).**
Resolve which change is meant, the staged diff, a commit range, or a branch against its base, and read the real diff for it, not the model's memory of the work.
Pick the altitude, a reviewer brief by default, with optional variants (a changelog line, a stakeholder note) only if asked.
Note criticality, whether the change touches money, auth, data, migrations, or a public API, which sets how hard to push blast radius and rollback.

**Phase 1 - Capture the actual change.**
Read the hunks, the changed files as they now stand, and the immediate surrounding code. Treat the commit message and branch name as assertions to verify in Phase 3, not as the source of truth.

**Phase 2 - Map the blast radius, grounded.**
For each changed symbol (function, type, endpoint, config key, schema), find its real dependents across the repo (call sites, importers, references) and classify each as affected, behavior changes for it, or unaffected, it compiles and behaves the same. Telling the reviewer what they do NOT need to worry about is as valuable as the affected list, and it is the cross-file reasoning the commodity summarizers skip.

**Phase 3 - Ground every claim (the E-ledger).**
For each statement the brief will make, attach evidence and a status. `verified` means tied to a specific hunk or a command output. `unverifiable` means it cannot be grounded from the diff or the tests, for example whether a new timeout matches an external SLA, or whether a downstream service tolerates a new payload shape. `unverifiable` claims never appear as fact, they go to the flagged section.
Run the tests that exercise the change and record the real result, so the "what to test" line is grounded in a run, not a promise.
Enforce the anti-parrot rule mechanically. If the diff does not show behavior X, the brief does not claim behavior X, no matter what the commit message says.
Optional runtime escalation. When tests exist and the language supports it, capture a real before-and-after of the changed path and ground the "what actually happens now" claims in it, borrowing microworld's real-trace discipline. Otherwise stay static but cited.

**Phase 4 - Compose the reviewer brief at altitude.**
Terse, high-signal, every line backed by an E-row. Sections.
- What changed and why. The "why" appears only if the code, a test, or a linked issue evidences it, otherwise it is omitted or flagged.
- Blast radius. The affected dependents, and explicitly the unaffected ones.
- What to test. With the real result if the test was run.
- Migration and rollback. A schema or data change names its reversal, otherwise "revert the commit, no state change."
- Unsure, flagged for the reviewer. The `unverifiable` rows as open questions, never smoothed.
Optional audience variants derive only from grounded rows and add no new claim.

**Phase 5 - Self-check, scope gate, and ban vague language.**
No line ships without a `verified` E-row or an explicit flag. The brief must stay scoped to the change and its dependents, and must not recap unchanged files or narrate the module, which is the scored scope gate. Ban "should work", "probably", "handles", and "seems", the confident vagueness this repo's verifier exists to catch, which therefore cannot appear in this skill's own output.
Optional closer, chain into adversarial-verify on the E-ledger, which re-checks each `verified` claim against its hunk or run and re-tests the blast-radius scoping.

## Suite integration

Claims are evidence-protocol assertions, prefix `E`, in the shared ledger, so adversarial-verify can audit an explain-changes brief directly, its E-ledger is already a verification packet.
This skill explains a change, it does not hunt for defects, so it routes security and correctness review to the installed code-review and differential-review skills and owns only the explanation dimension.
It complements fix-issue, which proves a specific bug fix holds, by writing the reviewer brief for any change, a feature, a refactor, or a fix, and can be chained after fix-issue to explain the fix it just made.

## Evals and testing plan

Artifacts in `evals/`, shared rules in [evidence-protocol.md](evidence-protocol.md).

- **Fixture checkout** (evals 1 and 2): a small Python checkout module with a seeded change delivered as a git patch, traps tuned so a frontier model cannot pass by reading the diff. The commit subject claims the change makes it so checkout totals can no longer go negative, but the clamp bounds only the percentage, so a negative subtotal from a negative-quantity line still yields a negative total, a subtle overclaim catchable only by a run or by tracing the subtotal. `api.final_price` reaches the changed function only through `checkout_total`, so a grep for the changed symbol misses it and the blast radius must be traced repo-wide. `reports.promo_preview` passes a fixed in-range percentage and is not reached by the clamp. The change adds money rounding whose agreement with the downstream processor is not derivable from the repo, the must-flag unverifiable. A passing test covers the happy path only, so verified-green must come from a real run and the negative-subtotal path grounded as untested. An unrelated module is a scope decoy.
- **Fixture logfix** (eval 3): a one-line change (a corrected log string) that guards the opposite failure, over-production. The correct output is a proportionate one-line brief with no invented blast radius and no ceremony.
- **Deterministic gates** (scored, >=3 reps, no-skill baseline arm, >=2 model tiers): blast-radius correctness on both the affected and the unaffected call site, the anti-parrot hard fail, the unverifiable-flag hard fail, grounded test result, scope restraint, rollback correctness, and no banned vague words.
- **Hard fails (pass^k, every rep).** Repeating the "handles negative quantities" claim as done is a hard fail. Asserting the rounding is correct rather than flagging it is a hard fail. Both are the fabricated-certainty failure mode, the same shape as cost-optimizer's no-derivable-volume hard fail.
- **RED baseline expectation.** The no-skill arm, or Claude Code's built-in PR summary, is expected to restate the totals-can-no-longer-go-negative claim since the clamp superficially supports it, scope the blast radius from a grep of the changed symbol and miss the transitive `api.final_price`, and assert or ignore the rounding rather than flag it. A capable model may still run the tests and find the direct callers, so the uplift concentrates on the transitive scoping, the subtle overclaim, and the unverifiable flag (evidence-protocol rule 6, prune what both arms pass while keeping the seed).
- **Trigger evals (separate, per evidence-protocol rule 5).** About 20 queries, 8 to 10 should-trigger ("explain what I'm shipping", "write the PR description for this change", "what does this diff actually do", "explain this change before I merge") against 8 to 10 near-miss should-not-trigger cases, the sharpest being "help me understand this whole module," which must route to microworld, and "review this PR for bugs," which must route to code-review. Each run 3 times, 60/40 train/test split so the description is not overfit.

## Out of scope

Finding defects or security holes (code-review and differential-review own that; this skill explains, it does not judge).
Whole-codebase onboarding or a deep learning artifact (microworld and the onboarding skills own that).
Posting to a PR or any external system (the skill produces the brief text, a human posts it).
