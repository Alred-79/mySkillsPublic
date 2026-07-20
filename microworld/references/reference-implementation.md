# The reference implementation: a described worked microworld

This file is the template to imitate, described inline so you can build a new world from this page alone.
It walks the shapes you produce in each phase - the world contract, the adapter, the capture-validate-build flow, and the trust gates - and grounds them in one real motivating example.

The motivating example is **Werkzeug's "Refactor the Multipart parsing into a Sans-IO layer"** (`cbb446fd`, parent `20dae301`).
That commit answers one causal question: as a multipart body streams in chunk by chunk, *when* does the new sans-IO decoder release part bytes, and *why* does a newline-free part release nothing until its closing boundary arrives, even though the old parser streamed it in roughly 1 KiB pieces?
The final form dict and file bytes are identical before and after, so a reviewer skimming tests sees "refactor" while the streaming, memory, and error behavior changed in several surprising ways.
That "identical output, different mechanism" quality is the ideal microworld target: the tests say refactor, the runtime behavior changed, and a confident wrong prediction is exactly what produces learning.

The rest of this file is generic. It describes the structures every world needs, using the multipart example only to make them concrete. Nothing here tells you to open another file - imitate the shapes below.

## (a) The world-definition / plan skeleton

Write the world contract *before* capturing anything. It is the plan the capture must later reproduce.
Its shape as a compact JSON object:

```jsonc
{
  "world": {
    "id": "werkzeug-multipart-sansio",
    "title": "When does the sans-IO multipart decoder release part bytes?",
    "causal_question": "Why does a newline-free part release nothing until its closing boundary arrives?"
  },
  "adapter": "adapter.py",              // path to the per-world adapter you write (Phase 1)
  "capture_repeats": 2,                  // run the whole capture at least twice; reject if the canonical runs differ
  "contract": {
    "included_state": [                  // keys the artifact may expose + input axes the learner varies
      "released_byte_offsets", "buffer_len_at_each_chunk", "event_stream", "final_form_dict", "exception"
    ],
    "omitted_state": [                   // deliberately out of the world; an omitted subsystem may appear only as an oracle
      "old_parser_internal_buffers"      // old path shown by OUTCOME only (oracle), mechanism untraced
    ],
    "boundary_mocks": "none",            // external seams declared mocked-boundary, or "none" for a closed world
    "invariants": [                      // what holds in every scenario, so the artifact can assert them
      "final_form_dict identical before and after the refactor"
    ],
    "cannot_claim": [                    // what this world does NOT establish -> seeds the unverified-surface report, becomes M rows
      "behavior on later Werkzeug versions",
      "performance or memory numbers under real load",
      "security properties",
      "any production-deployment behavior"
    ]
  },
  "prediction_rubric": {                 // how each typed prediction is graded against the captured run
    "released_before_boundary": { "type": "boolean", "result_path": "S2.released_byte_offsets.len_gt_0" },
    "write_count":              { "type": "number",  "result_path": "S1.buffer_len_at_each_chunk.count", "band": "write_count_band" }
  },
  "scenarios": {                         // the FOUR required roles - always all four
    "S1": { "role": "baseline",       "input": "multipart body with newlines, streamed in ~1 KiB chunks" },
    "S2": { "role": "counterfactual", "input": "same body but the target part has NO internal newline" },
    "S3": { "role": "failure",        "input": "truncated body: closing boundary never arrives" },
    "S4": { "role": "transfer",       "input": "same mechanism, different call site or new payload shape" }
  },
  "sandbox_grid": {                      // the declared free-manipulation space, captured as a full cross-product
    "causes": {                          // at most 2 manipulable causes, at most 4 values each
      "chunk_size":  [512, 1024, 4096],
      "has_newline": [true, false]
    }
    // cost = product of value counts, each cell captured twice and validated -> state this budget to the user at plan time
  }
}
```

The four scenario roles are non-negotiable and each has a job:

- **baseline** - the reference run the learner predicts first.
- **counterfactual** - the single intervention at the heart of the causal question (here: remove the newline). Viewed side by side with the baseline so the causal variable pops out.
- **failure** - where it breaks (here: the truncated body that never releases).
- **transfer** - the same mechanism at a new input or call site, used to test whether the learner's model generalized.

Two contract subtleties that the multipart world illustrates:

- **Oracle means mechanism-untraced, never output-invisible.** The old parser is omitted state, but its *outcomes* (it streamed the part in ~1 KiB pieces) still render, because that contrast is the lesson. You never hide the before-behavior; you only decline to trace its internals.
- **`cannot_claim` is load-bearing.** Each entry is a scope boundary that later seeds the adversarial-verify unverified-surface report and becomes an `M` ledger row. A scope exclusion is not verification residue, so write these deliberately.

## (b) The adapter function shape

The adapter imports the **real** implementation unmodified and drives it against the scenarios, emitting the events named in `included_state`.
The core is a `run_scenario(scenario, emit)` function: it runs the real code for one scenario and calls `emit(...)` once per observed-runtime event.
Every emitted event carries the value **as observed at runtime**, the **source line** it was observed at, and an **epistemic tag** (`observed-runtime` for real captures; `mocked-boundary` only for a declared seam - nothing else may ship).

```python
def run_scenario(scenario, emit):
    # 1. Import the REAL code, SHA-asserted, from the correct worktree.
    #    For a commit, put <worktree>/src on sys.path and assert HEAD == expected SHA.
    #    Never edit the source or monkeypatch the algorithm.
    assert current_head_sha() == scenario["expected_sha"]
    from werkzeug.sansio.multipart import MultipartDecoder   # the real symbol

    # 2. Instrument at the SEAM, not the algorithm. Subclass and call super()
    #    so the real method runs; record only what you OBSERVE around it.
    class ObservedDecoder(MultipartDecoder):
        def next_event(self):
            event = super().next_event()                      # real method runs unmodified
            emit(
                kind="event",
                value=observe(event),                         # value as actually produced
                source_line=lineno_of(super().next_event),    # where you observed it
                epistemic="observed-runtime",
            )
            return event

    # 3. Trace executed lines with sys.settrace scoped to the target file only,
    #    so you can later prove which lines ran within the declared symbol span.
    with line_tracer(scope="multipart.py") as traced_lines:
        decoder = ObservedDecoder(boundary=scenario["boundary"])
        for chunk in scenario["chunks"]:
            decoder.receive_data(chunk)
            emit(kind="buffer_len", value=len(decoder._buffer),
                 source_line=None, epistemic="observed-runtime")

    emit(kind="executed_lines", value=traced_lines, source_line=None,
         epistemic="observed-runtime")
```

Rules the adapter must honor (all illustrated by the multipart adapter):

- **Import the real code unmodified.** For a commit, use two git worktrees (before/after the SHA) and inject `<worktree>/src` onto `sys.path`. Assert `git rev-parse HEAD` equals the expected SHA before capturing.
- **Instrument at the seam.** Wrap public methods in a subclass whose overrides call `super()`; record buffer sizes, event types, and executed lines. Do not reimplement the algorithm to "check" it.
- **Run before/after in separate processes.** Two module trees must never collide in one interpreter - one subprocess per version.
- **Executed-line evidence is bounded.** Tracing proves a line *ran within the declared symbol span*. It is not proof that a given emitted byte was produced by that exact line. The artifact may say "these lines executed while this method ran"; it may not say "this byte was emitted by line 174" unless the emission itself was observed there.

An authorship pass typically re-runs the real decoder under the tracer to attach per-frame executed source lines, interns the distinct line sets (in the multipart world a handful of distinct sets covered thousands of frames), and embeds the verbatim symbol source with a matching file hash - so the artifact can show real code that is checkable against the traced file.

## (c) The capture -> validate -> build flow and the trust gates

The adapter runs in three modes, and they run in order. Nothing downstream may run until the gate above it passes.

1. **capture** - run every scenario plus the full sandbox-grid cross-product, at least twice, writing the raw runs to disk.
2. **validate** (the `check` release gate) - canonicalize the runs and enforce every gate below. This is where a broken world is caught.
3. **build** - splice the validated capture JSON into the artifact shell (a single HTML file with a `/*__CAPTURE_JSON__*/null` splice marker) to produce the playable artifact.

The trust gates the `check` step enforces, and what each one actually checks:

- **Determinism** - the double-capture is byte-identical after canonicalization. Canonicalize *only self-inflicted noise* (memory addresses, dict order, float repr, absolute paths under the source root). Never normalize timestamps, random values, or network-derived values - a path that depends on those must inject them as declared inputs or route them through a `mocked-boundary`, or it fails capture. If the two runs differ, stop, write both to disk, and name the likely nondeterministic seam. Do not average, do not pick one.
- **Ground truth** - captured values match the truth you probed when scoping the world (the multipart world established its expected offsets and write counts with a tiny probe script before any adapter existed). Any mismatch blocks the build.
- **Executed-line evidence** - every asserted line executed within its declared symbol span, and the embedded source hash matches the traced file.
- **Observer equivalence** - the result with the tracer/observer attached equals the result without it. The instrumentation must not change the behavior it records.
- **Secret hygiene** - pre-write redaction plus a payload/source secret scan; no credential-shaped strings in the capture.
- **Puppet-control check** - each declared intervention actually drives the captured states. A manipulable cause with no effect on any trace is a defect.
- **State fold/rewind/refold** - folding state forward, rewinding, and refolding yields hash-equal states, so the artifact's scrubbing is faithful.
- **Release epistemics** - every event is `observed-runtime` or a declared `mocked-boundary`; anything else fails closed.
- **Four scenario roles present** - baseline, counterfactual, failure, transfer.
- **Sandbox-grid coverage** - every sandbox-reachable state maps to a validated trace. This is what lets the artifact feel like free manipulation while only ever replaying captured cells.
- **Prose-provenance gate** - every behavior claim in model-written prose (background, consolidation, quiz feedback) cites a trace event id or an executed source line, or renders under the visible "author interpretation - not trace-verified" label.
- **Artifact verification** - the `verify` subcommand drives the built artifact headlessly (Playwright) and confirms every prediction submits, every reveal is prediction-gated, every control manipulates, every sandbox cell resolves to a captured trace, rewind reaches every state, and the quiz scores. Fails closed if Playwright is absent - install it rather than skip.

The full gate definitions, the schema v2 layout, and the canonicalization policy live in `protocol.md`; read it alongside this file when you write the adapter and run the gates.

## (d) A concrete walkthrough of the multipart example

Here is the whole flow on the one example, in prose, so the pattern is concrete.

The author picks the commit `cbb446fd` because it is an "identical output, different mechanism" refactor - the exact surprise the skill hunts for. Before writing any adapter, they write a tiny probe: run the real decoder on a small multipart body and record the ground truth (the byte offsets at which parts are released, the buffer length after each chunk, the final form dict). Those probed outputs become the values the capture must later reproduce.

They then write the world contract in the shape of section (a): the causal question, `included_state` (released offsets, per-chunk buffer lengths, the event stream, the final dict, any exception), `omitted_state` (the old parser's internals, shown by outcome only), `boundary_mocks: none` because the world is closed, the invariant that the final form dict is identical before and after, and a deliberate `cannot_claim` list (later versions, real-load performance, security, production behavior). They pick the four scenarios: S1 baseline (a body with newlines, streamed in ~1 KiB chunks), S2 counterfactual (the same body with the target part's internal newline removed), S3 failure (a truncated body whose closing boundary never arrives), and S4 transfer (the same mechanism at a new payload shape). The sandbox grid declares two causes - chunk size and whether the part has a newline - and the author states the capture cost (every cell captured twice and validated) up front.

Next the adapter (section (b)): it stands up two git worktrees at the parent and the commit, asserts each HEAD SHA, and injects each worktree's `src` onto `sys.path` in a *separate subprocess* so the two module trees never collide. It subclasses the real decoder, overriding the public methods to call `super()` and emit what it observes - buffer sizes, event types - each tagged `observed-runtime` with the source line it was seen at. A `sys.settrace` tracer scoped to `multipart.py` records which lines ran. It captures the whole scenario set plus the grid twice.

Then validation (section (c)): the two runs are canonicalized and diffed. The decisive finding on this world is the counterfactual - S2, the newline-free part, releases *nothing* until its closing boundary arrives, while S1 streamed its part out in ~1 KiB pieces, even though both end with the identical form dict. That is the safe-release rule the artifact will teach: the decoder emits only bytes provably before the last line break, so a part with no line break inside it is held back entirely until the boundary proves where it ends. Ground truth matches the probe, observer-equivalence holds, the grid is fully covered, and the epistemics are all `observed-runtime`. Only then does `build` splice the validated capture into the artifact, and `verify` drives it headlessly to confirm the interactions work.

## Read the honesty, not just the mechanics

The reference this file describes was built as a **prototype**, and its receipts said so where it mattered: `isolation: NONE - prototype, no sandbox-exec receipt`.
It demonstrated capture, determinism, executed-line evidence, and a validated playable artifact, but it did **not** produce the OS-sandbox receipt the hardened protocol specifies. That gap was stated, not hidden.

Take the same posture when you build.
The workflow and the protocol are proven on real code; a packaged general capture/build/check runtime and the sandbox receipt are the documented hardening layer, not a bundled binary you can assume is present.
Show what you captured, label what you did not, and never present a prototype shortcut as the full guarantee.
