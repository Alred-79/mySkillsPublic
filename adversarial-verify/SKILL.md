---
name: adversarial-verify
description: "Adversarially verify, stress-test, or red-team a previous agent's output before trusting it. Dispatches a blind verifier subagent that must re-derive the answer and try to refute each claim, rather than skim and agree. Use this whenever an agent (this one or another) has produced a code change, research answer, plan, or analysis and you want to check it for hallucinated citations, stale facts, subtle logic bugs, overconfident claims, or hidden assumptions - especially before shipping, merging, or acting on it. Trigger phrasings: \"verify this\", \"double-check that\", \"is this actually right\", \"stress-test the answer\", \"did the last agent hallucinate\", \"red-team this plan\", \"prove this claim\", \"audit these results\", \"check before I ship\". Reach for it even when the output \"looks fine\" - looking fine is exactly when a rubber-stamp slips through."
---

# Adversarial verify

Verify a previous agent's deliverable by dispatching a verifier that is built to refute it, not to agree with it. Works on any output type: a code diff, a research answer, a plan, an analysis.

## Why this works (read before running)

Two mechanisms carry the whole skill. Preserve them or the verification is theater.

**Blindness.** The verifier never sees the original agent's reasoning - no "because", no justification, no framing language. It gets the claims and the raw artifact, and must re-derive the answer from scratch. Reasoning is contagious: an argument that sounds right pulls a reader toward "yes" before they have checked anything. Strip the argument and the only path left is independent work. A second-order version of the same trap: the verifier must build its searches and queries from the claim's own terms, never by copying the artifact's phrasing, or the artifact's spin leaks into the check.

**Disprove-mandate.** The verifier's job is to find the failing case, not to confirm the passing one. "Looks reasonable" is not evidence and earns nothing. This matters because confirmation is cheap and refutation is expensive: an agent asked "is this right?" will find reasons it is, an agent asked "show me where this breaks" has to actually go look. The strongest form is a counterexample - a concrete failing input, command, or scenario. An argument can be talked around; a reproducible counterexample cannot.

Everything below is in service of those two ideas.

## Procedure

### 1. Extract the verification packet

Distill the target output into a packet the verifier can work from blind:

- **Claims**, numbered as assertion rows (see the ledger format below). One checkable statement each.
- **The artifact**: the diff, the file paths, the answer text, the plan - whatever is concretely being judged.
- **The output type**: code / factual / analysis. This routes the audit in step 3.

Do not carry over the original agent's reasoning or persuasion. If a claim only makes sense with its justification attached, that is a sign the claim is not yet checkable - rewrite it until it is.

### 2. Triage by risk

Rank each claim by blast radius if it is wrong: `high` / `medium` / `low`, recorded in the `risk` column. This is the verification budget. A wrong claim that silently corrupts data or ships a security hole gets the deep treatment; a cosmetic detail does not. Spend effort in risk order.

### 3. Stage 1 - blind audit

Dispatch the verifier with the packet only. Route by output type:

- **Code** - read the actual files (not the diff's description of them), run the tests, reproduce the behavior. Construct the input that breaks it.
- **Factual** - search independently. Check every date and version against today's date. Do not trust a number because it is specific.
- **Analysis** - hunt the unstated assumption, the internal contradiction, and the strongest alternative the answer ignored.

**Registry / existence sub-route (under factual).** For any claim that a package, tool, or library exists or is maintained, resolve the exact name against the live registry (npm / PyPI / crates.io / pkg.go.dev / Maven) and record the HTTP status plus one observed payload value - last-release date, archived flag. A name that does not resolve is `refuted`, not `unverifiable`: absence from the registry is positive evidence it is not real. This is the guard against hallucinated dependencies.

**Verification recipes.** When a claim ships with the exact command to re-run it, execute the command and diff the observed value against the claimed one. Do not eyeball it.

**Counterexample synthesis.** To refute, build the concrete failing case. Reach for a reproducible counterexample over a persuasive argument every time.

**Effort scaling.** Default: one verifier. On `high` effort: three verifiers on separate lenses - accuracy, freshness, groundedness. Two of three must pass for the claim to pass; when two or more lenses independently flag the same claim, escalate its severity - agreement across decorrelated checks is a strong signal.

Assign each claim a terminal status with cited evidence. Keep the statuses distinct: `refuted` means proven false (a counterexample, a failed check, or absence from a registry), `disputed` means credible evidence contradicts it without conclusively disproving it, and `unverifiable` means no evidence was found either way. All three are different findings, and neither `disputed` nor `unverifiable` is ever a pass.

### 4. Stage 2 - full-output review

Only if stage 1 passes. Now the verifier sees the original output verbatim and reads it as a hostile reviewer, looking for:

- Overclaiming - conclusions stronger than the evidence supports.
- Hedges that hide failures - "should work", "mostly", "in principle" covering a gap.
- Material omissions - the load-bearing caveat that was left out.
- Cross-claim patterns: citation padding (many sources, none load-bearing), a hotspot cluster (several weak claims leaning on one shaky fact), an authority mask (a confident tone standing in for evidence).

### 5. Verifier self-check

Any new finding the verifier raises is itself re-verified before it counts. A verifier can hallucinate a bug as easily as the original agent hallucinated a fact. A finding with no executed check behind it does not go in the report.

### 6. Verdict and unverified-surface report

Emit:

- **PASS / FAIL.**
- **Findings**, each with its evidence.
- **Unverified-surface report** - what could not be checked, and why. State the residual risk out loud. Never let silence imply "clean"; the things you did not check are exactly where the next failure hides.
- **Expiry tags** on freshness-sensitive claims (a version or "current as of" fact gets a re-check-after date).

Append the outcome to the verifier calibration log (a claim that passed here but later proved wrong is the highest-value entry - it tunes future skepticism).

### 7. Fix loop

On FAIL: fix the output, rebuild the packet, and dispatch a **fresh** verifier. Never reuse the one that just reviewed - it is anchored on what it already concluded and will defend it. Cap at three rounds; if findings still survive, report them honestly rather than burying them.

The final report bans "should work", "probably", and "seems". If a thing was verified, say so with the evidence. If it was not, say that instead. Confident vagueness is the exact failure mode this skill exists to catch, so it cannot appear in the skill's own output.

## The assertion ledger

Claims are rows in a markdown table (greppable, no tooling). This skill emits `A`-prefixed ids. The ledger persists in the repo being worked on (`.evidence/` or a task-local file) so it survives context compaction.

| id | assertion | status | evidence | expiry | risk |
|---|---|---|---|---|---|
| A1 | one checkable statement | `proposed` / `verified` / `refuted` / `disputed` / `unverifiable` | file:line, command + output, or URL + access date | date or `stable` | high / medium / low |

`refuted` = proven false (a counterexample, a failed check, or absence from a registry). `disputed` = credible evidence contradicts the claim without conclusively disproving it. `unverifiable` = no evidence found either way. They are different findings and neither `disputed` nor `unverifiable` is a pass. Every terminal status needs a citation - no citation, no status change.

Because the format is shared across this repo's skills, this skill can audit another skill's ledger directly: a fix-issue hypothesis ledger (`H` rows) or a revamp-ui design contract (`D` rows) is already a verification packet.

## The verifier agent

The verifier is defined in `agents/adversarial-verifier.md` - a hardened, read-only agent (Read, Grep, Glob, Bash, WebSearch, WebFetch; no edit tools) whose system prompt encodes the disprove-mandate and a named failure-mode taxonomy. Dispatch it via the Agent tool with the packet.

**Portability fallback.** If the `adversarial-verifier` agent type is not available in the current environment, dispatch a `general-purpose` subagent and paste the contents of `agents/adversarial-verifier.md` inline as its instructions. The behavior is identical; the custom agent type is a convenience, not a requirement.

## Invocation

`/adversarial-verify [target] [effort]`. No target means the last substantive deliverable. `effort` defaults to one verifier; `high` fans out to the three-lens panel.

Other skills chain into this one as an optional closer (fix-issue and revamp-ui both do) by dispatching the verifier on their own ledger.
