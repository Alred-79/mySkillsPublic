---
name: explain-changes
description: "Explain a code change at ship time so a human can trust it before it merges. Reads the real diff, grounds every claim in a specific hunk or a real test run, scopes the true blast radius across the repo (including what the change does NOT affect), and writes a terse reviewer-facing brief: what changed and why, what it touches, what to test, how to roll back, and what could not be verified. Use this whenever a change is about to ship and someone needs to understand or review it. Trigger phrasings: \"explain what I'm shipping\", \"write the PR description for this change\", \"what does this diff actually do\", \"explain this change before I merge\", \"summarize this commit for review\", \"is this change safe to merge\", \"draft release notes for this change\". Language-agnostic, one change at a time. This is NOT whole-codebase onboarding or a deep playable explainer, that is microworld, and it does NOT hunt for bugs or security holes, that routes to code-review; it explains and de-risks the specific change you are shipping, grounded strictly in the real diff and a real run, and honest about what it could not check."
---

# Explain changes

Explain the change you are about to ship, at the altitude a reviewer needs, with every line grounded in the real diff or a real run. Works on a staged diff, a commit range, or a branch against its base.

## Why this works (read before running)

Two mechanisms carry the whole skill. Preserve them or the brief is just another diff summary.

**Grounding.** Every line in the brief is tied to a specific hunk (`file:line`) or a real command output. The commit message, the branch name, and your own memory of the work are claims to check, never sources to copy. The agent that wrote the code is the worst-placed narrator of it, because it reports what it meant to do, and intent and code diverge exactly where the defect hides. A statement that cannot be tied to evidence is not stated as fact, it is flagged for the reviewer. This is the same discipline as microworld's every-number-from-a-trace and adversarial-verify's evidence-required.

**Reviewer altitude.** The brief answers only the questions a reviewer must resolve to decide whether to merge, and omits the ones the diff already answers. The per-file list of what changed is free and already on the PR page, so leave it out. The blast radius, the test result, and the rollback are what the reviewer cannot easily see, so surface those. A brief that drifts into a whole-repo tour is the noise that the paid PR bots are criticized for, and it fails the scope gate below.

Everything below serves those two ideas.

## Procedure

### 0. Scope the change and the audience (one light round; "go ahead" = infer)

Resolve which change is meant, the staged diff, a commit range, or a branch against its base, and read the real diff for it. Pick the altitude, a reviewer brief by default, plus a changelog line or a stakeholder note only if asked. Note criticality, whether the change touches money, auth, data, migrations, or a public API, which sets how hard to push blast radius and rollback.

### 1. Capture the actual change

Read the hunks, the changed files as they now stand, and the immediate surrounding code. Treat the commit message and the branch name as assertions to verify in step 3, not as the source of truth.

### 2. Map the blast radius, grounded

For each changed symbol (function, type, endpoint, config key, schema), find its real dependents across the repo (call sites, importers, references) and classify each as **affected**, its behavior changes, or **unaffected**, it compiles and behaves the same. Telling the reviewer what they do NOT need to worry about is as valuable as the affected list, and it is the cross-file reasoning a diff view cannot give them.

### 3. Ground every claim (the E-ledger)

For each statement the brief will make, attach evidence and a status.

- `verified` is tied to a specific hunk or a command output.
- `unverifiable` cannot be grounded from the diff or the tests, for example whether a new timeout matches an external SLA, or whether a downstream service tolerates a new payload shape. It never appears as fact, it goes to the flagged section.

Run the tests that exercise the change and record the real result, so the "what to test" line comes from a run, not a promise. Enforce the anti-parrot rule mechanically. If the diff does not show behavior X, the brief does not claim behavior X, no matter what the commit message says.

**Optional runtime escalation.** When tests exist and the language supports it, capture a real before-and-after of the changed path and ground the "what actually happens now" claims in it, borrowing microworld's real-trace discipline. Otherwise stay static but cited.

### 4. Compose the reviewer brief at altitude

Terse, high-signal, every line backed by an E-row. The brief scales to the change, a one-line change gets a one-line brief, and the ledger carries only the load-bearing claims, not every observation.

- **What changed and why.** The "why" appears only if the code, a test, or a linked issue evidences it, otherwise omit it or flag it.
- **Blast radius.** The affected dependents, and explicitly the unaffected ones.
- **What to test.** With the real result if the test was run.
- **Migration and rollback.** A schema or data change names its reversal, otherwise "revert the commit, no state change."
- **Unsure, flagged for the reviewer.** The `unverifiable` rows as open questions, never smoothed.

Optional audience variants (a changelog line, a stakeholder note) derive only from grounded rows and add no new claim.

### 5. Self-check, scope gate, and ban vague language

No line ships without a `verified` E-row or an explicit flag. Stay scoped to the change and its dependents, and do not recap unchanged files or narrate the module, that is the scope gate. Ban "should work", "probably", "handles", and "seems", the confident vagueness this repo's verifier exists to catch, which therefore cannot appear in this skill's own output.

**Optional closer.** Chain into adversarial-verify on the E-ledger. It re-checks each `verified` claim against its hunk or run and re-tests the blast-radius scoping.

## The assertion ledger

Claims are rows in a markdown table (greppable, no tooling). This skill emits `E`-prefixed ids. The ledger persists in the repo being worked on (`.evidence/` or a task-local file) so it survives context compaction.

| id | assertion | status | evidence | expiry | risk |
|---|---|---|---|---|---|
| E1 | one checkable statement about the change | `proposed` / `verified` / `unverifiable` | file:line hunk, or command + output | date or `stable` | high / medium / low |

`verified` needs a citation, a hunk or a run. `unverifiable` is a finding, never a pass, and it routes to the flagged section of the brief. Every terminal status needs a citation. No citation, no status change.

Because the format is shared across this repo's skills, adversarial-verify can audit an explain-changes brief directly, the E-ledger is already a verification packet.

## Boundaries and the funnel

explain-changes is the first pass. It briefs any change, in any language, at ship time. **Escalate to microworld** when the brief is not enough and the reviewer wants to inhabit a path and watch it run, which microworld does as a playable traced artifact for Python. **adversarial-verify audits either one.** It re-derives and tries to refute the claims in an E-ledger (this skill) or an M-ledger (microworld), so the deeper the tier the harder the check.

**Not a defect hunter, but never silent.** This skill explains a change, it does not run a full defect or security scan, so when the ask is "find what is wrong with this," route to code-review or differential-review. But if you notice something that looks wrong while explaining, flag it in a line and point there. Explaining a change honestly includes saying when it looks broken; withholding that to stay in lane would make the brief worse than a plain read. What routes away is the systematic hunt, not the observation.

## Invocation

`/explain-changes [target]`. No target means the staged diff, or the last commit if nothing is staged. A target may be a commit range or a branch name to diff against its base.

fix-issue can chain into this skill to write the reviewer brief for the fix it just proved.
