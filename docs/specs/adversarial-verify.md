# Spec: adversarial-verify

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

Generic adversarial verification of a previous agent's output: stress-test, verify, or
improve any deliverable (code change, research answer, plan/analysis) by dispatching a
blind verifier subagent that must re-derive rather than agree.

Market position (researched 2026-07): the space is crowded but partitioned - blindness
exists code-only (superpowers requesting-code-review), refute-mandates exist inline-only
(GitHub doublecheck), claims-audits exist documents-only (fact-check v0.2 gist),
anti-groupthink panels exist without fix loops (agent-review-panel). **No skill combines
the reasoning-stripped packet + blind refuter + type routing + effort scaling + fresh-
verifier fix loop.** Full comparison in the research notes of this repo's history.

## Files

```
adversarial-verify/
  SKILL.md                        # orchestration procedure
  agents/adversarial-verifier.md  # hardened verifier agent definition (Claude Code)
  evals/                          # colocated evals (layout per evidence-protocol.md):
    evals.json                    #   cases; fixtures/ = seeded artifacts + clean controls;
    fixtures/  expected.md        #   expected.md = planted-defect ground truth
```

Fallback rule (portability): if the `adversarial-verifier` agent type is unavailable,
dispatch a general-purpose subagent with the same prompt inline. SKILL.md is self-contained.

## Flow

1. **Packet extraction (blindness mechanism).** Orchestrator distills the target output
   into a verification packet: numbered claims (evidence-protocol assertion rows), the
   artifact (diff / file paths / answer text), output type. **No reasoning, no "because"
   from the original agent.** Second-order defense (from fact-check v0.2): the verifier
   must build searches/queries from claim metadata, never from the artifact's framing
   language.
2. **Risk triage.** Rank claims by blast-radius-if-wrong (high/medium/low in the ledger);
   verification effort follows ranking.
3. **Stage 1 - blind audit.** Dispatch verifier(s) with the packet. Type routing:
   code → read actual files, run tests, reproduce; factual → independent search, check
   dates/versions against today; analysis → hunt unstated assumptions, contradictions,
   strongest ignored alternative. **Registry/existence sub-route (under factual):** for
   any claim that a package/tool exists or is maintained, resolve the exact name against
   the live registry (npm/PyPI/crates.io/pkg.go.dev/Maven) and paste the HTTP status +
   an observed payload value (last-release date, archived flag); a name that does not
   resolve is `refuted`, not `unverifiable`. When the packet ships a verification recipe
   (an assertion row carrying the exact command to re-run - as better-tools does), the
   verifier executes it and diffs the observed value against the claimed one. Verdict statuses per evidence protocol, including the
   **disputed vs unverifiable** split. **Counterexample synthesis:** to refute, construct
   the concrete failing input/command/scenario - an argument can be wrong, a reproducible
   counterexample can't. Effort scaling: 1 verifier default; `high` → 3 lenses (accuracy /
   freshness / groundedness), 2-of-3 to pass, severity escalates when 2+ lenses agree.
4. **Stage 2 - full-output review** (only if stage 1 passes). Verifier sees the original
   verbatim; checks overclaiming, hedges hiding failures, material omissions, and the
   named cross-claim patterns (citation padding, hotspot cluster, authority mask).
5. **Verifier self-check.** Any NEW finding the verifier introduced is itself re-verified
   (guards verifier hallucination - borrowed from agent-review-panel's post-judge gate).
6. **Verdict.** PASS/FAIL + findings + **unverified-surface report** (what could not be
   checked and why - residual risk stated, never implied clean). Freshness-sensitive
   claims get expiry tags. Outcomes append to the calibration log.
7. **Fix loop.** On FAIL: orchestrator fixes, rebuilds packet, dispatches a **fresh**
   verifier (never reuse - anchoring). Max 3 rounds; then report surviving findings
   honestly. Final report bans "should work / probably / seems" phrasing.

## Verifier agent hardening

System prompt: job is to refute; "looks reasonable" is not evidence; agreeing earns
nothing; empty findings require executed checks with outputs shown. Give it the named
failure-mode taxonomy to hunt: ghost citation, quote drift, paraphrase inflation,
overconfident specificity, temporal confusion, fabricated precision. Tools: Read, Grep,
Glob, Bash, WebSearch, WebFetch - no edit tools. Optional: cross-model verifier for
decorrelated blind spots.

## Invocation

`/adversarial-verify [target] [effort]` - no target = last substantive deliverable.
Callable from other skills via `REQUIRED SUB-SKILL: adversarial-verify` (fix-issue and
revamp-ui both chain into it).

## Evals & testing plan

Eval architecture (artifacts in `evals/`; shared rules in
[evidence-protocol.md](evidence-protocol.md)): seeded-defect artifacts + **clean
controls**. Metrics: recall on planted defects, false-positive rate on clean inputs,
per-defect-category breakdown - golden answers are correct here, the defect list IS
ground truth. Graded **pass^k** (a verifier that catches the bug 1-in-3 runs is a
broken gate), ≥3 reps, deterministic grading throughout; negative controls are
non-optional (a verifier that flags everything is useless).

TDD cycle - RED: baseline a verifier-less agent on the fixtures (planted stale fact,
subtle bug, overclaim), document rubber-stamp rationalizations verbatim. GREEN: skill
catches all seeded errors, blesses the clean controls. REFACTOR: counter each observed
rationalization in the verifier prompt.
