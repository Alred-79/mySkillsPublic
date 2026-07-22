# Spec: microworld

Status: approved design, pre-implementation. Adversarially reviewed 2026-07-19; all 15
findings resolved in this revision.
Triggers narrowed 2026-07-22 to explicit deep-learning intent so microworld and
explain-changes do not collide on a bare "explain this diff" request. microworld is the
deep tier explain-changes escalates to, and adversarial-verify audits either ledger.
Depends on: [evidence-protocol.md](evidence-protocol.md)
Origin: user-supplied draft (protocol.md + SKILL.md, Codex-authored MVP) inspired by
Geoffrey Litt, "Understanding is the new bottleneck" (geoffreylitt.com, 2026-07-02).
The draft's trust layer is kept in full; this spec adds the pedagogy layer, the runtime
build plan, and suite integration.

## Purpose

Turn one real Python code path into a validated, rewindable, prediction-first learning
artifact - so a human can *understand* AI-written code by inhabiting it, not reading
about it. The agent captures real execution traces of baseline / counterfactual /
failure / transfer scenarios, validates determinism and provenance, and builds a
self-contained browser artifact where the user predicts before seeing, manipulates
captured causes, compares counterfactuals side-by-side, and exits through a
comprehension gate.

## Market position (researched 2026-07)

- **The intersection is empty.** AppMap: real traces, no pedagogy. Litt's /explain-diff
  + codebase-to-course: pedagogy, no execution. Python Tutor: real execution + rewind,
  toy snippets only. rr/Pernosco: determinism, zero learning framing. Swimm: freshness
  validation of text references, not behavior. No tool combines real-trace grounding +
  repo-native code paths + interactive pedagogy.
- **Litt did not publish this.** He shipped a skill only for explainer docs; his
  micro-worlds were bespoke one-offs with no protocol, validation story, or repo. This
  is the first published, validated, reproducible microworld protocol (macOS-hosted
  capture in v1 - see scope).
- **The real-execution differentiator is evidence-backed**: CRUXEval - frontier models
  <70% at predicting outputs of 3–13-line Python functions; EE-Eval (arXiv 2606.31012)
  - AI-generated explorables routinely ship broken interactions; trace-grounded
  rationales reduce hallucination (arXiv 2503.05703).
- **The problem is real**: comprehension-debt RCT - AI-assisted engineers matched
  completion time but scored 17% lower on comprehension quizzes; Osmani's
  "Comprehension Debt"; Litt's cognitive-debt framing.

## Files

```
microworld/
  SKILL.md                 # workflow + authoring guidance + non-negotiables
  references/protocol.md   # hardened capture/validation protocol - draft text plus the
                           #   enumerated v2 deltas listed below (otherwise verbatim)
  references/pedagogy.md   # learning-loop design rules + evidence notes
  scripts/microworld.py    # runtime: capture | build | check | verify | serve
  assets/template/         # artifact shell (viewer, prediction UI, quiz components)
  assets/demo/             # minimal working example plan + adapter
  evals/                   # colocated evals (layout per evidence-protocol.md)
```

**Protocol deltas from the draft (complete list - everything else is verbatim):**
`schema_version: 2` adds the `pedagogy` block and `sandbox_grid`; the `check` gate list
gains the pedagogy gates, the prose-provenance gate, and artifact verification; the
runtime gains the `verify` subcommand. No trust clause is weakened.

## Trust layer (draft, kept in full)

`scripts/microworld.py` implements the draft protocol: sandbox-exec capture with
embedded receipt (network + writes denied; unsupported hosts fail closed;
`--allow-unisolated-execution` diagnostic-only and cannot validate); ≥2 identical
captures or rejection; independent Python line events (an adapter-asserted line is
accepted only if it executed within the declared symbol span - this is executed-line
evidence, **not proof the emission was temporally correlated with that exact line**);
observer/no-observer result equivalence; pre-write redaction + payload/source secret
scan; puppet-control check; state fold/rewind/refold hash equality; freshness hashing
(plan, adapter, fixtures, deps, sources, runtime, git state); release epistemics
`observed-runtime` / declared `mocked-boundary` only, all else fail-closed; the four
scenario roles; `cannot_claim`; no-mastery-verdict rule.

Two draft caveats carried forward verbatim into SKILL.md and the user-facing report:
Python guards are defense in depth, **not the security boundary** - process execution
and file reads remain allowed, so **adapters always require human review** and must
never point at production credentials or systems.

**Trace canonicalization policy** (load-bearing for the determinism gate): normalize
only self-inflicted noise - memory addresses/object ids, dict iteration order, float
repr, and absolute paths under source_root. Timestamps, random values, and network
nondeterminism are NOT normalized: code paths depending on them must inject them via
declared inputs or `mocked-boundary` seams, or they fail capture. Strictness is the
point; the failure message tells the author which seam to declare.

## Pedagogy layer (schema v2 `pedagogy` block; every element evidence-graded)

Guided learning loop (guided-discovery beats sandbox and lecture - Alfieri 2011;
Kirschner/Sweller/Clark 2006):

1. **Background before prediction** - minimal context so a committed prediction is
   possible (Brod 2021: uninformed guesses produce no learning).
2. **Committed prediction with confidence** - specific predicted outcome + confidence,
   captured **immediately before that scenario's own reveal** (per-scenario timing;
   transfer items are predicted at their step, after the mechanism is learned).
   Scenario selection targets surprise - author the world around the code path's most
   expectation-violating behavior.
3. **Observe real execution** - trace replay, rewind/scrub.
4. **Self-explanation prompt** (g=0.55) - "why did that happen?" about the system,
   never about the learner's own understanding.
5. **Manipulate + counterfactual, side-by-side** (contrasting cases). Implicit
   scaffolding: guidance lives in what is manipulable and starting configurations;
   every manipulable element labeled.
6. **Consolidation - "a time for telling"** - an explicit explanation names the
   mechanism (cases without telling reliably underperform).
7. **Graded transfer**: near (same code, new input) and medium (same mechanism,
   different call site) items are **captured `transfer`-role scenarios** - real traces,
   real answer keys. Far transfer (different subsystem) cannot be trace-grounded under
   the one-world schema, so it ships as an **ungraded open question with no revealed
   answer claim**, listed in `cannot_claim`. Transfer is diagnostic + learning event,
   never a mastery verdict.
8. **Exit gate: retrieval quiz with per-answer feedback** (testing effect; Litt's
   speed regulator). **Quiz items ARE typed prediction fields**: each behavioral item
   declares a `result_path` resolving against a captured scenario, validated by the
   same `check` gate as predictions. Conceptual (non-behavioral) items are explicitly
   flagged `conceptual: true` and carry no behavior claim.
9. **Sandbox last - the captured intervention grid.** Free-feeling manipulation in a
   replay-only artifact requires pre-captured coverage: the plan's `sandbox_grid`
   declares ≤2 manipulable causes × ≤4 values each; capture runs the full
   cross-product (every cell twice, validated like any scenario); `check` verifies
   every sandbox-reachable state maps to a validated trace. Grid cost is stated to the
   author at plan time. The artifact ends with the far-transfer open question the
   learner owns.

**Prose-provenance gate (release gate, in `check`)**: every behavior claim in
model-written prose - background, consolidation, quiz feedback - must cite a trace
event id or an executed source line; uncited behavior claims either fail `check` or
render under a visible "author interpretation - not trace-verified" label. Same
mechanism as statistician's provenance-ID grep. Without this, the pedagogy layer could
smuggle in exactly the model-simulated behavior claims the trust layer disqualifies.

**Artifact verification (`verify` subcommand, part of the release gate)**: drives the
artifact headlessly via Playwright - every prediction field submits, every reveal is
prediction-gated, every control manipulates, every sandbox cell resolves, rewind
reaches every state, quiz scores. **Fails closed if Playwright is absent**; SKILL.md
instructs installation. A broken microworld teaches wrong lessons about real code.

## Dry-run lessons (2026-07, Werkzeug multipart artifact - binding on SKILL.md)

1. **The change is the story.** The artifact must establish what/why/where/impact
   through interaction before the mechanism: the commit as a visible event (real
   stats, cited purpose), the system position (pipeline scene), and the OLD behavior
   as a first-class visible counterfactual. "Oracle" in the contract means
   mechanism-untraced, never output-invisible - before-outcomes must render.
2. **Playthrough, not document.** Stepped pages of prose ≈ textbook regardless of
   interactivity density. The artifact is a continuous operable system with goals:
   the user tampers (drags, installs the change, routes inputs, tunes limits) and
   consequences are large and visible. Text = labels, tickers, tooltips, mission
   briefs ≤2 lines; no rendered paragraph >240 chars outside collapsed details.
3. **Register is elicited, not assumed.** Gamified-vs-professional tone and page-vs-
   flow structure are user preferences; ask one AskUserQuestion round (like revamp's
   dials) before building. Default: professional instrument with playthrough goals.
4. **Capture requirements proven out**: authorship grid (dense enough that authored
   inputs snap to real cells), per-frame executed-line interning (16 traces covered
   5648 frames), counterfactual summary per cell, consistency-gated richer oracle
   traces. The `verify` Playwright gate caught real bugs both runs - non-negotiable.

## Invocation

`/microworld [question or code path]` - e.g. "why does checkout retry twice on
timeout?". Given only a path, the skill helps select a question: prefer code paths
where (a) recent AI-written changes landed, (b) behavior likely violates a reasonable
prior, (c) the causal story fits a reduced world. One question per world.

## Suite integration (evidence-protocol mapping)

Microworld emits assertions with prefix `M` to the working repo's ledger: the isolation
receipt, each freshness hash, and each `check` gate result become `verified` rows citing
the check output; freshness rows carry `expiry` = "on any source/dependency/runtime/git
change". `cannot_claim` entries **seed** the unverified-surface report when
adversarial-verify audits a microworld ledger - they do not replace it (scope exclusion
≠ verification residue).

## Evals & testing plan

Artifacts in `evals/`; shared rules incl. trigger evals in
[evidence-protocol.md](evidence-protocol.md).
- **Viability gate (deterministic, pass^k)**: on fixture repos (small Python projects
  with a seeded surprising behavior), capture ×2 identical, `check` passes, `verify`
  passes.
- **Protocol compliance (deterministic)**: predictions gate reveals; four roles +
  pedagogy block present; prose-provenance gate enforced; no undeclared epistemics.
- **Fidelity probe**: grader independently executes fixture code and diffs actual
  outputs against artifact behavior claims - **zero tolerance scoped to
  `observed-runtime` events**; for `mocked-boundary` events the grader checks
  declaration completeness (seam named, mock visible in the artifact UI), not
  behavioral equality (mocks differ from reality by design).
- **Explanation quality (judged)**: blind pairwise judging of the **textual layer
  only** - the consolidation explanation vs a static explainer given the same trace
  facts (interactive-vs-static can't be anonymized, and affordances are already
  deterministically checked). A true comprehension comparison (simulated learner or
  human protocol) is explicitly future work.
- **RED baseline** (writing-skills TDD): agent without the skill asked to "help me
  understand this code interactively" - expected failures: model-simulated behavior
  claims, sandbox dumped on the user, no prediction gating, broken interactions.
  GREEN: gates catch all seeded traps. REFACTOR: close loopholes.

## Out of scope (v1; mirrored in `cannot_claim` and the user-facing report)

Python-only. **macOS-only capture** (sandbox-exec receipts required; Linux
bwrap/landlock is future work; note: sandbox-exec is Apple-deprecated - migration risk
accepted for v1). Single-process; no distributed causality, external-mock fidelity, or
production-safety claims; browser replays recorded re-executions only; far transfer
ungraded. The report always lists which checks passed and what the world omits.
