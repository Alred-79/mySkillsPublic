# Spec: fix-issue

Status: approved design, pre-implementation
Depends on: [evidence-protocol.md](evidence-protocol.md)

## Purpose

Meta-debugging orchestrator: user describes a problem, invokes `/fix-issue`, and the
skill runs a rigorous, complexity-gated debugging process — sequential for shallow bugs,
a competing-hypotheses swarm for hard ones.

Market position (researched 2026-07): the market converged on single-agent
hypothesis→instrument→reproduce→fix→cleanup (Cursor Debug Mode, VS 2026 @debugger,
mattpocock diagnose, many SKILL.md clones). IDE vendors win shallow bugs via runtime
access. **Nothing ships: a complexity gate, competing-hypothesis subagents with a
disprove mandate, a persistent evidence ledger, differential-diagnosis ranking, or a
bug-type routing table.** This skill's territory is the hard-bug tier; do not race IDEs
on shallow bugs. Note: `/debug` name is taken (Claude Code built-in, debugs Claude Code
itself). Installed `/root-cause-investigation` is a business-metrics skill — unrelated.

## Files

```
fix-issue/
  SKILL.md                          # triage → route → investigate → fix → verify
  hypothesis-ledger.md              # ledger template (evidence-protocol format)
  agents/hypothesis-investigator.md # optional read-only investigator agent (Claude Code)
  evals/                            # colocated evals (layout per evidence-protocol.md):
    evals.json                      #   fixtures/ = planted-bug mini-projects + red herrings;
    fixtures/  expected.md          #   expected.md = root causes + required gates per case
```

Hybrid dependency rule (used throughout): "if skill X is installed, invoke it; otherwise
apply the inline procedure below." Self-contained for downloaders; upgraded by
superpowers / Trail of Bits when present.

## Flow

**Phase 0 — Triage (always, cheap).**
- Restate the bug in one sentence. Grep `bugs-learned.md`: seen this class before?
- **Feedback loop first** (from mattpocock diagnose): construct a deterministic,
  agent-runnable pass/fail signal before any hypothesis work. If repro steps are missing,
  synthesize a minimal reproducer rather than blocking (from VS @debugger).
- Stale-report check: referenced files/paths still exist? diff history since report.
- Classify: logic / regression / flaky-timing / performance / memory / build-CI /
  environment-config / security-shaped.
- **Complexity gate:** clear error + obvious recent suspect → stay sequential (vendored
  systematic-debugging: read errors fully, git diff, instrument boundaries, single
  hypothesis, minimal test). Most bugs end here.

**Routing table (by class).** regression → `git bisect run` with the pass/fail command;
flaky → condition-based-waiting + state-pollution bisect; perf → profile first, never
guess; security-shaped → semgrep/codeql + fp-check if installed, else inline taint
checklist.

**Phase 1 — Swarm (gated: genuine uncertainty, multi-component, or first sequential
hypothesis refuted; `deep` flag forces it).**
- Write 3–5 competing hypotheses into the ledger. **Pre-registration:** each records its
  predicted observation before any experiment runs.
- Dispatch one **read-only** investigator per hypothesis in parallel, one message. Brief:
  repro steps + your single hypothesis + mandate to **disprove** it. Skeptic asymmetry
  framing: wrongly confirming your hypothesis costs double.
- Fixed lenses join when relevant: git-historian, environment-checker ("check the plug"),
  log-forensics.
- Instrumentation: NDJSON debug lines tagged with hypothesis IDs inside `#region DEBUG`
  markers — evidence machine-checkable, cleanup greppable.
- Synthesis: differential-diagnosis ranking — next experiment is the cheapest one that
  *discriminates* between survivors. Prediction-vs-actual deltas recorded.
- **Tarpit detection:** same files re-read, new hypotheses isomorphic to refuted ones →
  force a perspective break (fresh agent with zero prior framing, or the environment lens).

**Phase 2 — Fix.** Root cause confirmed → failing test (red) → minimal single fix
(green). **Falsify the fix:** deliberately re-break the code and confirm the new test
catches it (verify the test, not just the fix), then restore. Remove all `#region DEBUG`
instrumentation — checklist item. Iron laws vendored: no fixes without root cause; one
variable at a time; 3 failed fixes → stop and question architecture with the user.

**Phase 3 — Verify.** Original repro passes; full suite fresh, output read. Closer:
`REQUIRED (if available): adversarial-verify`. **Auto-autopsy:** emit a post-mortem
(root cause, why missed, what discriminated) → appends to `bugs-learned.md`.

## Evals & testing plan

Eval architecture (artifacts in `evals/`; shared rules in
[evidence-protocol.md](evidence-protocol.md)), two layers:
- **Outcome** (binary, automated): planted failing behavior passes post-fix, full suite
  green, red herring not chased.
- **Process**: from the transcript, check **gates passed — never step sequences**
  (strict trajectory matching is brittle; agents find valid unanticipated routes):
  reproduced before fixing, root cause stated before patch, instrumentation cleaned,
  verification run before "done". Plus continuous signals: thrashing cycles, turns,
  tokens (a first-try fix reflects better process at equal outcomes).
- Report pass@k for hard bugs and pass^k for the gates; ≥3 reps, no-skill baseline.

TDD cycle — RED: baseline agent on the planted multi-component bug + red herring —
expected failures: jumps to fix, anchors on one hypothesis, chases the red herring,
leaves debug logging in. GREEN/REFACTOR: verify gate, disproof mandate, ledger upkeep,
cleanup, falsify-the-fix all hold.
