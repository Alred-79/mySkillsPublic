# Microworld pedagogy: the learning loop and why each step is there

The design rules for the prediction-first artifact, and the learning-science evidence behind each step. Read this before building the artifact (Phase 2). The point is not to decorate a trace viewer with quiz widgets; it is to run a specific sequence that the evidence says produces durable understanding, where a plain explainer produces the illusion of it.

The one non-negotiable is **guided discovery**, not free exploration and not a lecture. A guided loop where the learner predicts, is surprised by a real result, and is then told the mechanism beats both a sandbox dumped on the user (too little structure) and a wall of prose (no commitment, no surprise). Every rule below serves that shape.

## The loop, step by step, with the why

### 1. Background before prediction

Give the minimum context needed to make a *committed* prediction possible, and no more. An uninformed guess produces no learning: if the learner has no basis to predict, "predicting" is a coin flip and the surprise that follows teaches nothing. So supply just enough - the setup, the input, the question - that the learner can form a real expectation. Over-explaining here is as harmful as under-explaining: say too much and you have given away the answer, and there is nothing left to be surprised by.

### 2. Committed prediction with confidence

The learner commits to a **specific, typed** outcome and a **confidence**, captured **immediately before that scenario's own reveal**. This is the engine of the whole artifact. A learner who has publicly committed and is then contradicted by a real result experiences a prediction error that drives them to restructure their mental model - the same restructuring that passively watching the correct answer never triggers. Confidence matters because a high-confidence miss is the most productive event in the loop: it marks exactly the belief that was wrong.

Timing is per-scenario, not up front. Predict scenario S right before S's reveal, so the commitment is fresh and specific. Transfer items are predicted at their own step, *after* the mechanism has been taught, because their job is to test whether the mechanism transferred.

Choose the scenario to **maximize surprise**. Author the world around the code path's most expectation-violating behavior. A prediction the learner gets right by default teaches little; a confident prediction the real trace overturns teaches a lot. This is why Phase 0 hunts for "the tests say refactor but the runtime changed" diffs.

### 3. Observe the real execution

Replay the captured trace, with rewind and scrub. This is the payoff of the commitment and the moment the trust rule earns everything: the learner sees what the code *actually did*, not a claim about it. Rewind lets them re-watch the exact instant their prediction broke.

### 4. Self-explanation prompt

Ask "why did that happen?" about the **system**, never about the learner's own understanding. Self-explanation is among the highest-leverage things a learner can do (a large positive effect on comprehension; the spec cites g=0.55), because putting the causal chain into words forces the gaps to surface. Aim it at the mechanism ("why did the parser hold everything back?") not at metacognition ("do you understand?"), because explaining the system builds the model while rating your own understanding does not.

### 5. Manipulate and counterfactual, side by side

Show contrasting cases **together**, differing in one cause. Two runs viewed side by side make the causal variable pop out; the same two runs viewed one after another do not, because working memory cannot hold the first well enough to diff it against the second. This is why the counterfactual is a first-class scene, not a footnote.

Scaffolding here is **implicit**: the guidance lives in *what is manipulable* and in the starting configuration, not in a paragraph of instructions. Constrain the manipulable space to the causes that matter, start it in a revealing state, and label every manipulable element. The learner discovers the rule by moving the right knobs, which is more durable than being told it.

### 6. Consolidation - a time for telling

After the contrasting cases, give an **explicit explanation that names the mechanism**. This is the step novices' intuition says to skip and the evidence says to keep: discovery *without* telling reliably underperforms. The sequence matters. The contrasting cases first prepare the ground - they create the question the telling answers - and then the explicit naming of the mechanism ("this is the safe-release rule: emit only bytes provably before the last line break") lands and sticks. Skip the telling and the insight stays fuzzy; lead with the telling and there was no question for it to answer.

### 7. Graded transfer

Two grounded tiers plus one honest ungrounded one:

- **Near transfer** - same code, new input. A captured `transfer`-role scenario with a real trace and a real answer key.
- **Medium transfer** - same mechanism, a different call site. Also a captured `transfer`-role scenario, real trace, real key.
- **Far transfer** - a different subsystem. This **cannot** be trace-grounded under the one-world schema, so it ships as an **ungraded open question with no revealed answer claim**, and it is listed in `cannot_claim`.

Transfer is a **diagnostic and a learning event, never a mastery verdict**. It shows the learner (and the artifact) whether the mechanism generalized; it does not certify competence.

### 8. Exit gate - retrieval quiz with per-answer feedback

A short retrieval quiz with immediate per-answer feedback. This uses the testing effect (retrieval strengthens memory more than re-reading) and doubles as the learner's own speed regulator: getting an item wrong is the signal to slow down and re-engage, replacing the false "I read it, I get it" fluency.

**Quiz items ARE typed prediction fields.** Each behavioral item declares a `result_path` that resolves against a captured scenario and is validated by the same `check` gate as the predictions - so a quiz item cannot assert a behavior the traces do not support. Conceptual (non-behavioral) items are explicitly flagged `conceptual: true` and carry no behavior claim; they test understanding of the idea, not a specific captured value.

### 9. Sandbox last - the captured intervention grid

End with free-feeling manipulation, backed entirely by the pre-captured `sandbox_grid`. This resolves the replay-only paradox: manipulation feels open, but every reachable state was captured and validated in advance, so the artifact never simulates. The check gate proves every sandbox-reachable state maps to a real trace. Put the sandbox last, after the mechanism is learned, so the learner is exploring with a model rather than flailing. The artifact closes on the far-transfer open question the learner now owns.

## Two rules from the dry run (binding on the artifact)

These came out of the Werkzeug dry run and are not optional.

- **The change is the story.** Before any mechanism, establish what/why/where/impact through interaction: the commit as a visible event (real stats, cited purpose), the system position (where this sits in the pipeline), and the OLD behavior as a first-class visible counterfactual. "Oracle" (mechanism-untraced) never means output-invisible - the before-outcomes must render, because the contrast *is* the lesson.
- **Playthrough, not document.** A stepped sequence of prose pages is a textbook regardless of interactivity density. Build a continuous operable system with goals: the learner tampers (drags, installs the change, routes inputs, tunes limits) and the consequences are large and visible. Text is labels, tickers, tooltips, and mission briefs of two lines or less. No rendered paragraph over ~240 characters outside a collapsed details block. If the learner is reading more than doing, the design has drifted back into a textbook.

## Register is elicited, not assumed

Gamified-versus-professional tone and page-versus-flow structure are **user preferences**, not defaults you get to pick silently. Ask one `AskUserQuestion` round before building, the way a UI-revamp asks for dials. Default, if the user defers: a **professional instrument with playthrough goals** - an operable debugger-like surface, not a cartoon, but still a thing you *play*, not a thing you read.

## The provenance line the pedagogy must not cross

The pedagogy layer is where model-written prose lives (background, consolidation, quiz feedback), which makes it the most likely place for a simulated behavior claim to sneak in. Hold the line: every behavior claim in that prose cites a trace event id or an executed source line, or it renders under the visible "author interpretation - not trace-verified" label. This is the prose-provenance gate in `references/protocol.md`. It is what keeps the pedagogy honest - without it, a persuasive paragraph could assert behavior the code never exhibited, which is exactly the failure the whole skill exists to prevent.

## Evidence notes

The design rests on a small, convergent literature (named in the spec):

- **Guided discovery beats pure discovery and pure instruction** - Alfieri et al. 2011; Kirschner, Sweller & Clark 2006. The loop is guided on purpose.
- **Predictions must be informed to help** - Brod 2021: uninformed guesses produce no learning, which is why background precedes prediction.
- **Self-explanation is high-leverage** - a large positive effect on comprehension (the spec cites g=0.55), aimed at the mechanism.
- **Contrasting cases and "a time for telling"** - contrasting cases prepare the learner, and an explicit telling afterward is what consolidates; discovery without telling underperforms.
- **Testing effect** - retrieval practice with feedback outperforms re-reading, and regulates the learner's pace.
- **The problem is real and specific to AI-assisted work** - a comprehension-debt result where AI-assisted engineers matched completion time but scored materially lower on comprehension; frontier models themselves score under 70% at predicting outputs of short Python functions (CRUXEval), which is the same prediction gap the artifact trains a human to close. AI-generated explorables routinely ship broken interactions, which is why Phase 3's `verify` gate is non-negotiable.
