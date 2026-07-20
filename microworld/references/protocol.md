# Microworld capture and validation protocol (schema v2)

The hardened protocol that makes "replay real traces only" enforceable rather than aspirational. This is the release contract: a microworld ships only when every gate here passes, or it does not ship. It supersedes any older draft protocol.

Read this when writing the adapter (Phase 1) and when running the check gates. `references/reference-implementation.md` describes a working instance of everything below - the adapter shape, the capture-validate-build flow, and each gate on a real Werkzeug commit - with its shortfalls (no OS sandbox receipt) recorded honestly. Read it alongside this file as the self-contained concrete template.

## Contents

- [The one invariant](#the-one-invariant)
- [Release epistemics: two labels, everything else fails closed](#release-epistemics)
- [Isolation and the sandbox-exec receipt](#isolation-and-the-sandbox-exec-receipt)
- [The security boundary (verbatim)](#the-security-boundary)
- [Determinism: double-capture and canonicalization](#determinism)
- [Executed-line evidence (and what it does not prove)](#executed-line-evidence)
- [Schema v2: the pedagogy block and the sandbox grid](#schema-v2)
- [The check gates (the release gate list)](#the-check-gates)
- [The verify subcommand (artifact self-verification)](#the-verify-subcommand)
- [Freshness hashing and the M ledger](#freshness-hashing)
- [What this protocol does not cover (v1 scope)](#v1-scope)

<a id="the-one-invariant"></a>
## The one invariant

Every value the artifact displays - a state, an event, a buffer length, an outcome, an exception - is either observed at runtime during a validated capture, or explicitly labeled author interpretation. There is no third category. A number that was neither captured nor labeled is a release-blocking defect, because the entire warrant of a microworld is that it shows what the code *actually did*. A fabricated value that happens to look right is the worst outcome: it teaches a confident wrong lesson about real code.

Everything in this document exists to make that invariant checkable by a gate rather than trusted on the author's word.

<a id="release-epistemics"></a>
## Release epistemics: two labels, everything else fails closed

Every event carries an `epistemic` tag. Only two values may ship:

- `observed-runtime` - the value was recorded while the real implementation executed during a validated capture. This is the default and the overwhelming majority.
- `mocked-boundary` - the value crosses a declared external seam (a network call, a clock, a paid API) that the world stubs on purpose. The seam must be named in the world contract's `boundary_mocks`, and the mock must be visible in the artifact UI so the learner knows this part is a stand-in, not reality.

Any other provenance - inferred, assumed, computed-in-the-browser, author-guessed - is **not** a shippable epistemic. It fails the check gate closed. Author commentary is allowed, but only as clearly labeled interpretation attached to real events, never as a synthesized event in the trace stream.

<a id="isolation-and-the-sandbox-exec-receipt"></a>
## Isolation and the sandbox-exec receipt

The hardened capture runs the adapter under `sandbox-exec` (macOS) with a profile that **denies network and denies writes** outside a scratch directory, and embeds a **receipt** recording the profile, the interpreter, the worktree SHAs, and the traced-source hashes. Unsupported hosts **fail closed**: if the sandbox cannot be established, the capture cannot be validated.

- `--allow-unisolated-execution` is **diagnostic-only** and **cannot validate** a world. It exists so an author can iterate on a machine without the sandbox, but a capture produced under it is not a releasable capture and must be marked as such.
- The reference implementation runs *without* the sandbox and records this truthfully: its `receipts.json` says `isolation: NONE - prototype, no sandbox-exec receipt`. That honesty is the point. A packaged runtime that produces the real receipt is the documented hardening layer; do not claim it is present when it is not.

macOS-only for v1. Linux `bwrap`/landlock is future work. `sandbox-exec` is Apple-deprecated; the migration risk is accepted for v1 and stated in the report.

<a id="the-security-boundary"></a>
## The security boundary (verbatim)

Carry these two sentences into the SKILL body and the user-facing report unchanged:

> Python guards are defense in depth, **not the security boundary** - process execution and file reads remain allowed, so **adapters always require human review** and must never point at production credentials or systems.

The sandbox reduces blast radius (no network, no stray writes); it does not make an arbitrary adapter safe to run unseen. A human reads the adapter before it runs. It never points at anything real.

<a id="determinism"></a>
## Determinism: double-capture and canonicalization

A world that is not deterministic under its adapter cannot be replayed faithfully, so nondeterminism is a **hard capture failure**, not a warning.

1. Run the full capture (all scenarios plus the sandbox grid) **at least twice**.
2. Canonicalize each run and compare byte-for-byte. If they differ, stop: write both runs to disk for inspection and fail with a message naming the likely nondeterministic seam. Do not average results and do not pick one run.

**Canonicalization policy (load-bearing - normalize only self-inflicted noise):**

- **Normalize:** memory addresses and object ids, dict iteration order, float repr, and absolute paths under `source_root`. These are artifacts of the observation, not of the code's behavior.
- **Do NOT normalize:** timestamps, random values, network-derived values. A code path that depends on these is depending on real nondeterminism. It must inject them as declared inputs, or route them through a `mocked-boundary` seam, or it fails capture. The failure message tells the author which seam to declare. Strictness is the point: the discipline is what guarantees the replay matches reality.

<a id="executed-line-evidence"></a>
## Executed-line evidence (and what it does not prove)

To ground a claim that a specific source line ran, the adapter traces execution with `sys.settrace` scoped to the target file and records the set of line numbers that executed. An adapter-asserted line is accepted **only if it executed within the declared symbol span**.

Be precise about the strength of this evidence. It is **executed-line evidence**: proof the line ran during the traced call. It is **not** proof that a given emitted event was temporally correlated with that exact line. The artifact may say "these lines executed while this method ran"; it may not claim "this byte was emitted by line 174" unless the emission itself was observed at that point. Overstating this is a provenance defect.

Intern distinct executed-line sets to keep the capture small (the reference augmentation covered thousands of frames with a handful of distinct sets), and embed the verbatim source of the symbols that actually execute, with line numbers and a matching file hash, so the artifact shows real code.

<a id="schema-v2"></a>
## Schema v2: the pedagogy block and the sandbox grid

`schema_version: 2` extends the trust-layer capture with exactly two additions; no trust clause is weakened.

- **`pedagogy` block** - the learning-loop content: per-scenario background, the typed prediction fields with their `result_path`s, the self-explanation prompts, the consolidation text, the graded transfer items, and the quiz items (behavioral items typed like predictions; conceptual items flagged `conceptual: true`). Every behavior claim in this block is subject to the prose-provenance gate.
- **`sandbox_grid`** - the declared intervention space: at most 2 manipulable causes, at most 4 values each. Capture runs the **full cross-product**, every cell twice, validated like any scenario. The grid's cost is stated to the author at plan time because it is the compute budget. `check` verifies every sandbox-reachable state maps to a validated trace - this is what lets the artifact feel like free manipulation while only ever replaying captured cells.

Typed prediction fields (in scenarios and quiz items alike) declare a `result_path` that resolves against the captured run record. Grading is exact match for booleans and enums; numbers are exact because the world is deterministic (band a number only when the world contract bands it, e.g. a `write_count_band`).

<a id="the-check-gates"></a>
## The check gates (the release gate list)

`check` is the release gate. All of these must pass:

1. **Determinism** - the double-capture is byte-identical after canonicalization.
2. **Ground truth** - captured values match the truth probed when the world was scoped; any mismatch blocks the build.
3. **Executed-line evidence** - every asserted line executed within its declared symbol span; the embedded source hash matches the traced file.
4. **Observer equivalence** - the result with the observer/tracer attached equals the result without it. The instrumentation must not change the behavior it records.
5. **Secret hygiene** - pre-write redaction plus a payload/source secret scan; no credential-shaped strings in the capture.
6. **Puppet-control check** - the declared interventions actually drive the captured states (a manipulable cause with no effect on any trace is a defect).
7. **State fold/rewind/refold** - folding the state forward, rewinding, and refolding yields hash-equal states, so the artifact's scrubbing is faithful.
8. **Release epistemics** - every event is `observed-runtime` or declared `mocked-boundary`; anything else fails closed.
9. **Four scenario roles present** - baseline, counterfactual, failure, transfer.
10. **Pedagogy gates** - the `pedagogy` block is present and well-formed; predictions gate reveals; transfer items are graded (near/medium) or declared ungraded (far); no undeclared epistemics leak in through prose.
11. **Sandbox-grid coverage** - every sandbox-reachable state maps to a validated trace.
12. **Prose-provenance gate** - see below.
13. **Artifact verification** - the `verify` subcommand passes (see below).

**Prose-provenance gate (release gate).** Every behavior claim in model-written prose - background, consolidation, quiz feedback - must cite a trace event id or an executed source line. This is the same mechanism as a provenance-ID grep over an analyst's report: grep the prose for behavior claims, require each to carry a citation. An uncited behavior claim either fails `check` or renders under a visible "author interpretation - not trace-verified" label. Without this gate the pedagogy layer could smuggle in exactly the model-simulated behavior claims the trust layer disqualifies, which would defeat the whole skill.

**No-mastery-verdict rule.** The artifact never certifies that the learner has mastered anything. Transfer is a diagnostic and a learning event; the quiz gives per-answer feedback. Neither is a competency judgment, and the artifact must not present one.

<a id="the-verify-subcommand"></a>
## The verify subcommand (artifact self-verification)

`verify` drives the built artifact **headlessly via Playwright** and asserts it actually operates:

- every prediction field submits;
- every reveal is prediction-gated (you cannot see the answer before committing);
- every control manipulates the state it claims to;
- every sandbox cell resolves to a captured trace;
- rewind reaches every state;
- the quiz scores.

**Fails closed if Playwright is absent** - the SKILL instructs installing it rather than skipping. This gate caught real interaction bugs on both dry-run builds. A microworld that renders but misbehaves teaches wrong lessons about real code, so `verify` is part of the release gate, not optional polish.

<a id="freshness-hashing"></a>
## Freshness hashing and the M ledger

Hash the inputs that make the capture reproducible: the plan, the adapter, the fixtures, the dependencies, the traced sources, the runtime, and the git state. If any of these change, the capture is stale and must be re-run.

Emit `M`-prefixed rows to the working repo's ledger (evidence-protocol.md):

- the isolation receipt, as a `verified` row citing the receipt;
- each freshness hash, as a `verified` row whose `expiry` = "on any source/dependency/runtime/git change";
- each `check` gate result, citing the check output.

The `cannot_claim` entries **seed** the unverified-surface report when adversarial-verify audits a microworld ledger; they do not replace it. A scope exclusion is not the same as verification residue, so the audit still enumerates what it could not check.

<a id="v1-scope"></a>
## What this protocol does not cover (v1 scope)

State these limits in the report; they also populate `cannot_claim`:

- **Python-only.** No other language runtime is captured.
- **Single-process.** No distributed causality, no cross-service traces.
- **macOS-only sandbox receipt.** Linux isolation is future work; `sandbox-exec` is Apple-deprecated.
- **No external-mock fidelity claim.** A `mocked-boundary` differs from reality by design; the gate checks the mock is *declared and visible*, not that it behaves like the real dependency.
- **No production-safety claim.** The browser replays recorded re-executions of a reduced world; it says nothing about a real deployment.
- **Far transfer is ungraded.** It ships as an open question with no revealed answer, listed in `cannot_claim`.
