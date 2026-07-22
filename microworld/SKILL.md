---
name: microworld
description: "Build a playable, prediction-first learning artifact from ONE real Python code path or commit, so a person can inhabit how it behaves at runtime instead of reading a summary. It captures real execution traces (baseline, counterfactual, failure, transfer), proves they truly ran and are deterministic, then builds a browser artifact where the learner predicts before seeing, manipulates the captured causes, and exits through a comprehension gate. Every displayed number comes from a real trace, never a simulation. This is the deep tier. Reach for it to SEE a behavior run or to learn a gnarly algorithm, not for a routine explanation. Trigger phrasings: \"build an interactive explainer for this\", \"make a microworld for this parser or function\", \"I want to really understand how this behaves\", \"let me play with this code path\", \"teach me this by running it\". For a fast ship-time brief on a change you are shipping, use explain-changes and escalate here only when a brief is not enough. adversarial-verify audits the artifact's claims. Python-only, single-process, macOS for the sandbox receipt."
---

# Microworld

Turn one real Python code path into a validated, rewindable, prediction-first learning artifact. The learner predicts what the code will do, then watches the *real* captured trace prove them right or wrong, manipulates the captured causes, and leaves through a comprehension gate. Understanding is the bottleneck for AI-written code; this closes it by making the learner inhabit the execution instead of reading a summary.

This is the deep tier of change explanation. explain-changes gives the fast ship-time brief for review, and you reach for microworld when that brief is not enough and you want to watch the behavior run. adversarial-verify audits either one's ledger.

## The trust rule (read this first - it is the whole point)

**Replay real captured traces only. Never simulate behavior.** Every number, state, event, and outcome the artifact shows must come from a real execution of the real implementation, captured to disk and validated, or be explicitly labeled author interpretation. The instant the artifact displays a plausible-looking value the code never actually produced, the skill has failed at its one job: a broken or fabricated microworld teaches a *wrong* lesson about real code, which is worse than no microworld at all.

Concretely, this forbids three tempting shortcuts:

- **No hand-authored trace values.** You do not write `write_sizes = [5000]` because it seems right. You run the code, observe `[5000]`, and store what you observed. If you never ran it, you cannot show it.
- **No JavaScript that re-implements the algorithm.** The artifact's interactivity is *lookup into pre-captured cells*, not a model of the parser running in the browser. When the user drags a slider, the artifact fetches the trace that was captured for that input; it does not compute a new one.
- **No prose behavior claim without a citation.** Background, consolidation, and quiz feedback may only assert behavior that cites a trace event id or an executed source line. Anything else renders under a visible "author interpretation - not trace-verified" label, or fails the release gate.

If the environment cannot capture a real trace for something (a code path that depends on the clock, the network, or randomness), you do not fake it. You either inject that dependency as a declared input, declare it as a `mocked-boundary` seam that the artifact shows as a mock, or you cut it from the world. Strictness is the feature. See `references/protocol.md` for the full validation gates and canonicalization policy that make this enforceable.

## What ships in v1 (honest scope - state this to the user)

v1 ships the **validated workflow, the hardened protocol, and a proven reference implementation** - not a one-command runtime binary. Concretely:

- **You build the per-project capture adapter yourself**, following `references/protocol.md`, exactly as the described reference implementation did for a real Werkzeug commit. There is no general `capture` binary that works on an arbitrary repo unseen; the adapter is short, per-world, and always requires human review (see the security boundary below). `references/reference-implementation.md` describes the worked example inline as a self-contained template - the adapter shape, the capture-validate-build flow, and the trust gates - so you can imitate it from that file alone.
- **A packaged general capture/build/check runtime and OS-sandbox receipts are the documented hardening layer, not a bundled artifact.** The protocol specifies them (schema v2, the sandbox-exec receipt, the `verify` gate); the reference implementation records honestly where it stops short (its receipts say `isolation: NONE - prototype`). Do not claim a runtime you did not build.
- **Constraints:** Python-only. Single-process (no distributed causality). macOS-only for the sandbox-exec receipt (Linux bwrap/landlock is future work; sandbox-exec is Apple-deprecated, a risk accepted for v1). The user-facing report always lists which checks passed and what the world omits.

**Security boundary (verbatim, non-negotiable).** The adapter executes real code and reads real files. The Python-level guards are defense in depth, **not the security boundary** - process execution and file reads remain allowed. Therefore **adapters always require human review** and must never point at production credentials or systems. Say this in the report.

Never present model-authored behavior as captured. Every displayed value comes from a real trace or is labeled author interpretation. This is the line the whole skill defends.

## Workflow

Four phases. Phase 0 picks the world. Phase 1 captures and validates real traces. Phase 2 builds the prediction-first artifact. Phase 3 verifies the artifact drives correctly. Do not build the artifact (Phase 2) until Phase 1's gates pass - an artifact on top of unvalidated traces is the exact failure this skill exists to prevent.

### Phase 0 - Pick one causal question and the reduced-world contract

One world answers **one causal question**. Given a bare code path, help the user choose one where (a) recent AI-written changes landed, (b) the behavior likely violates a reasonable prior, and (c) the causal story fits a small closed world (bytes in, observable states out). The best worlds are "identical output, different mechanism" diffs: the tests say refactor, the runtime behavior changed. Surprise is the design target - author the world around the code path's most expectation-violating behavior, because an uninformed guess produces no learning but a *violated* confident prediction produces a lot.

Write the **world contract** before capturing (the world-definition skeleton in `references/reference-implementation.md` is the template):

- `causal_question` - the single "why does X happen?" answerable by tracing this implementation.
- `included_state` - the keys the artifact will expose (states, events, final values, exceptions) and the input axes the learner can vary.
- `omitted_state` - everything deliberately out of the world. An omitted subsystem may appear only as a behavioral **oracle** (its outputs shown, its mechanism untraced). Oracle means mechanism-untraced, never output-invisible: if the old code path is the contrast, its *outcomes* must still render.
- `allowed_interventions` - what the learner may change (payload bytes, chunk schedule, a limit, the entry point). Everything manipulable is captured coverage (see the sandbox grid).
- `boundary_mocks` - external seams declared as `mocked-boundary`, or none if the world is closed.
- `invariants` - what holds in every scenario, so the artifact can assert them.
- `cannot_claim` - what this world does NOT establish (later versions, unprobed features, performance, security, production behavior). These seed the unverified-surface report and become `M` ledger rows.

Pick the **four scenario roles**: `baseline` (the reference run), `counterfactual` (the one intervention at the heart of the causal question), `failure` (where it breaks), and `transfer` (same mechanism, new input or call site). Then declare the `sandbox_grid`: at most 2 manipulable causes, at most 4 values each. State the grid's capture cost to the user now - every cell is captured twice and validated like any scenario, so the cross-product is the compute budget.

### Phase 1 - Write a fixed adapter, capture real runtime events, validate

Write an adapter that **imports the REAL implementation** and drives it against the scenarios, emitting the observed-runtime events named in `included_state`. The adapter shape (a `run_scenario(scenario, emit)` function) in `references/reference-implementation.md` is the pattern:

- **Import the real code unmodified.** For a commit, use two git worktrees (before/after the SHA) and inject `<worktree>/src` onto `sys.path`. Assert `git rev-parse HEAD` equals the expected SHA before capturing. Never edit the source or monkeypatch the algorithm.
- **Instrument at the seam, not the algorithm.** Wrap the public methods in a subclass whose overrides call `super()` so the real methods run; record what you observe (buffer sizes, event types, executed lines via a `sys.settrace` tracer scoped to the target file). Executed-line evidence proves a line ran within the declared symbol span; it is not proof the emission was temporally tied to that exact line. Record every value as observed at runtime.
- **Run before/after in separate processes.** Two module trees must never collide in one interpreter; one subprocess per version.
- **Capture at least twice and reject nondeterminism.** Canonicalize both runs (normalize only self-inflicted noise; see the policy in `references/protocol.md`) and diff. If they differ, the world is not deterministic under this adapter - **fail the capture** and tell the author which seam to declare. Do not average, do not pick one.
- **Verify against probed ground truth.** Compare captured values against the truth you recorded when scoping the world. Any mismatch stops the build; never paper over it.

Then run the **check gates** from `references/protocol.md`: identical double-capture, executed-line evidence, observer/no-observer equivalence, secret redaction, sandbox-grid coverage (every reachable state maps to a validated trace), freshness hashing, and the release epistemics (`observed-runtime` or declared `mocked-boundary` only; everything else fails closed). Emit the isolation receipt, each freshness hash, and each gate result as `M` rows to the working repo's ledger (evidence-protocol.md).

### Phase 2 - Build the prediction-first playthrough artifact

Build a self-contained browser artifact (single HTML file, capture JSON spliced in) that runs the **pedagogy loop**. The loop is not decoration; each step earns its place from learning-science evidence, and `references/pedagogy.md` gives the full rules and citations. Read it before building. The order:

1. **Background before prediction** - minimal context so a *committed* prediction is possible. An uninformed guess produces no learning, so give just enough to make the guess real, no more.
2. **Committed prediction with confidence** - a specific typed prediction plus a confidence, captured **immediately before that scenario's own reveal**. Prediction-before-reveal is the engine: a learner who has publicly committed and is then surprised restructures their model in a way that passively watching never triggers. Transfer items are predicted at their own step, after the mechanism is taught.
3. **Observe the real execution** - replay the captured trace with rewind and scrub. This is the payoff of the commitment: the real behavior, not a claim about it.
4. **Self-explanation prompt** - "why did that happen?" about the *system*, never about the learner's own understanding. Self-explanation is one of the highest-leverage study moves; asking it about the mechanism forces the causal chain into words.
5. **Manipulate and counterfactual, side by side** - contrasting cases shown together. Two runs that differ in one cause, viewed together, make the causal variable pop out in a way sequential viewing does not. Guidance is implicit: it lives in *what is manipulable* and the starting configuration, and every manipulable element is labeled.
6. **Consolidation - a time for telling** - an explicit explanation that *names the mechanism*. Discovery without telling reliably underperforms: the learner needs the contrasting cases first (so the telling lands on prepared ground) and then the name, or the insight stays fuzzy.
7. **Graded transfer** - near (same code, new input) and medium (same mechanism, new call site) items are **captured `transfer`-role scenarios** with real traces and real answer keys. Far transfer (a different subsystem) cannot be trace-grounded here, so it ships as an **ungraded open question with no revealed answer**, listed in `cannot_claim`. Transfer is a diagnostic and a learning event, never a mastery verdict.
8. **Exit gate - retrieval quiz with per-answer feedback** - the testing effect, and the learner's own speed regulator. **Quiz items ARE typed prediction fields**: each behavioral item declares a `result_path` that resolves against a captured scenario and is validated by the same gate as predictions. Conceptual items are flagged `conceptual: true` and carry no behavior claim.
9. **Sandbox last - the captured intervention grid** - free-feeling manipulation, backed entirely by the pre-captured grid. The artifact ends on the far-transfer open question the learner now owns.

Two rules from the dry run, binding on the artifact:

- **The change is the story.** Establish what/why/where/impact through interaction before the mechanism: the commit as a visible event (real stats, cited purpose), the system position, and the OLD behavior as a first-class visible counterfactual.
- **Playthrough, not document.** A stepped wall of prose is a textbook no matter how many widgets it has. Build a continuous operable system with goals: the learner tampers (drags, installs the change, routes inputs, tunes limits) and consequences are large and visible. Text is labels, tickers, tooltips, and mission briefs of two lines or less; no rendered paragraph over ~240 characters outside a collapsed details block.

Before building, elicit register in **one** `AskUserQuestion` round: gamified vs professional tone, page-by-page vs continuous-flow structure. Default to a professional instrument with playthrough goals.

**Prose-provenance gate (release gate).** Every behavior claim in model-written prose must cite a trace event id or an executed source line, or render under the visible "author interpretation - not trace-verified" label. Without this, the pedagogy layer would smuggle in exactly the model-simulated behavior claims the trust rule disqualifies. Full gate in `references/protocol.md`.

### Phase 3 - Artifact self-verification

Drive the built artifact headlessly (Playwright) and confirm it actually works: every prediction field submits, every reveal is prediction-gated, every control manipulates, every sandbox cell resolves to a captured trace, rewind reaches every state, and the quiz scores. **This fails closed if Playwright is absent** - install it rather than skipping. The dry run's `verify` gate caught real bugs on both runs; a microworld that looks right but misbehaves teaches wrong lessons, so this is non-negotiable, not optional polish.

## The report

Close with a report the user can trust:

- The causal question and what the world established.
- Which check gates passed, with the isolation receipt and freshness hashes (`M` rows).
- **What the world omits** - the `cannot_claim` list, verbatim, as the unverified surface. Never let silence imply the world proves more than it does.
- The security-boundary and honest-scope statements above, so the user knows the adapter needs review and that no simulated runtime is being claimed.

Chain `adversarial-verify` on the `M` ledger as a closer: it audits the artifact's claims, and the `cannot_claim` entries *seed* its unverified-surface report (they do not replace it).

## References

- `references/protocol.md` - the hardened capture/validation protocol: schema v2, every check gate, epistemics, the sandbox-exec receipt, and the canonicalization policy. Read it when writing the adapter and running the gates. Supersedes any older draft.
- `references/pedagogy.md` - the learning-loop design rules and the evidence behind each step. Read it before building the artifact.
- `references/reference-implementation.md` - a self-contained described worked template (world contract, adapter shape, capture -> validate -> build flow, trust gates) grounded in a real Werkzeug commit. Read it to learn the pattern from one page; imitate the inline structures rather than opening any external example.
