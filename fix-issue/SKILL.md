---
name: fix-issue
description: "Debug and fix a reported bug end to end - reproduce it, find the true root cause, patch it, and prove the fix holds. Use whenever a user hands you a defect and wants it resolved: \"debug this\", \"why is X failing\", \"fix this bug\", \"this test is flaky\", \"the endpoint returns the wrong number\", a stack trace, a failing CI job, or any unexpected behavior they want chased down and corrected. Reach for it even when the user does not say the word \"debug\" but is clearly describing something broken. Escalates hard, multi-component, or contested bugs to a competing-hypotheses subagent swarm so you do not anchor on the first plausible cause. This is NOT Claude Code's built-in /debug (which debugs Claude Code itself) - this fixes bugs in the user's own project."
---

# fix-issue

You are fixing a bug in the user's project. The failure mode this skill exists to prevent is the confident wrong fix: you latch onto the first plausible cause, patch a symptom, declare victory, and the bug survives (or a new one is born). Everything below is built to make that failure hard.

The core discipline: **no fix without a reproduced failure and a confirmed root cause.** A green test you never saw fail proves nothing.

## How to use this skill

Work the phases in order. Phase 0 is always cheap and always runs. Most bugs are shallow and end inside Phase 0 - do not over-ceremony a typo. The heavy machinery (Phase 1 swarm) is gated: you spend it only when a bug earns it. Track evidence in a ledger from the moment you have more than one candidate cause.

Read `hypothesis-ledger.md` when you open the ledger (Phase 1). Read `agents/hypothesis-investigator.md` when you dispatch investigators.

### Hybrid dependency rule

Throughout, some steps name a companion skill. The rule is always: **if that skill is installed, invoke it; otherwise apply the inline procedure given right there.** This skill is fully self-contained - the named skills are upgrades, not requirements. Never claim you ran a tool you do not have.

---

## Phase 0 - Triage (always, cheap)

The goal of triage is a reproduction and a classification, fast, before any theorizing.

1. **Restate the bug in one sentence.** Force yourself to name the observed-vs-expected gap concretely. "The `/checkout` total is $4.10 when the cart should sum to $4.00" beats "checkout is broken." Vague restatements hide the bug.

2. **Grep `bugs-learned.md` (repo root, if present): seen this class before?** Past autopsies from this skill land there. A prior entry can hand you the discriminating evidence for free. If the file does not exist yet, skip - it gets created in Phase 3.

3. **Build the feedback loop first.** Before any hypothesis work, construct a deterministic, agent-runnable pass/fail signal for the bug - a single command you can run that fails now and will pass when fixed. This is the spine of the whole process: every later step checks itself against this signal.
   - If the user gave repro steps, turn them into that command.
   - If repro steps are missing or vague, **synthesize a minimal reproducer** rather than blocking on the user. A failing test that isolates the behavior is worth more than a paragraph of description. Get to red.

4. **Stale-report check.** Do the referenced files, paths, and line numbers still exist? `git log` / `git diff` the relevant area since the report was filed. Reports rot; you may be chasing a bug that was already moved or fixed.

5. **Classify the bug.** Pick the closest: logic / regression / flaky-timing / performance / memory / build-CI / environment-config / security-shaped. The class routes you (next section) and sharpens your priors.

6. **Complexity gate - decide sequential vs swarm.** Be honest about how much you actually know:
   - **Clear error message + one obvious recent suspect** (a specific file changed, a stack trace points home): stay **sequential**. Read the error in full, `git diff` the suspect, add instrumentation at the boundary, form a single hypothesis, write the minimal failing test, fix, verify. Most bugs end here. Do not summon a swarm to fix an off-by-one.
   - **Genuine uncertainty, multiple plausible components, or the failure crosses subsystems**: go to **Phase 1** (the swarm).
   - If the user passed a `deep` flag, force Phase 1 regardless.

If sequential resolves it: skip to Phase 2 for the fix discipline, then Phase 3 to verify and record.

### Routing table (by class)

Apply the row for your class. Each names a companion skill under the hybrid rule.

| Class | Route |
|---|---|
| **regression** | `git bisect run <pass/fail command>` to pin the introducing commit automatically. The feedback loop from step 3 *is* the bisect predicate. Read the culprit commit before theorizing about mechanism. |
| **flaky-timing** | Do not "add a retry." Find the race. If `condition-based-waiting` is installed, use it; else replace every sleep/poll with an explicit wait-for-condition, and bisect for **state pollution** across tests (run the failing test alone, then after its neighbors, to see if order matters). |
| **performance** | **Profile first, never guess.** Attach a profiler / add timing spans and let measurement name the hot path. Optimizing an unprofiled guess is how you speed up the wrong thing. |
| **security-shaped** | If `semgrep` / `codeql` / `fp-check` (Trail of Bits) are installed, run them and triage findings for false positives. Otherwise apply an inline taint walk: trace each untrusted input to every sink (query, exec, deserialize, file path, template) and check the sanitization in between. Do not fix a "vuln" you have not shown is reachable. |
| logic / memory / build-CI / environment-config | Proceed to the complexity gate result; instrument the relevant boundary. |

---

## Phase 1 - Competing-hypotheses swarm (gated)

Enter here only when the gate sent you (real uncertainty, multi-component, `deep` flag, or your first sequential hypothesis was refuted).

**Why a swarm instead of just thinking harder.** A single reasoner anchors: it forms one hypothesis and then reads the evidence to confirm it. Confirmation bias is not a character flaw you can will away - it is structural. Running several investigators in parallel, each owning a *different* hypothesis and each tasked to **disprove its own**, breaks the anchor. The point is not more compute; it is decorrelated views that cannot all be wrong the same way. Preserve that independence - do not let them share a conclusion before the evidence is in.

1. **Write 3-5 competing hypotheses into the ledger** (`hypothesis-ledger.md` format, evidence-protocol rows, ids `H1`, `H2`, ...). Make them genuinely different mechanisms, not one idea reworded. Each hypothesis row **pre-registers its predicted observation before any experiment runs** - what you expect to see in logs/state if this hypothesis is the cause. Pre-registration is what makes the later "predicted vs actual" delta meaningful; a prediction written after you peeked is worthless.

2. **Dispatch one read-only investigator per hypothesis, in parallel, in a single message.** Each gets: the repro steps, the pass/fail command, its one assigned hypothesis, and the mandate to **disprove it**. Use the brief in `agents/hypothesis-investigator.md`. Skeptic-asymmetry framing goes in every brief: **wrongly confirming your hypothesis costs double wrongly killing it** - a false "yes, this is the cause" sends the whole fix down the wrong hole, so when in doubt, try harder to falsify. Investigators are read-only: they observe and instrument, they do not patch.

3. **Add fixed lenses when relevant** (also read-only, dispatched alongside):
   - **git-historian**: what changed around when this started - blame, recent diffs, suspicious commits.
   - **environment-checker** ("check the plug"): versions, env vars, config, dependency lockfile drift, "works on my machine" gaps. Bugs love the boring cause.
   - **log-forensics**: existing logs/traces/crash dumps read carefully before adding new ones.

4. **Instrument with machine-checkable evidence.** Emit debug lines as NDJSON (one JSON object per line) tagged with the hypothesis id, wrapped in greppable markers so cleanup is trivial:

   ```
   #region DEBUG H2
   print(json.dumps({"h": "H2", "loc": "cart.subtotal", "pre": items, "out": total}))
   #endregion DEBUG H2
   ```

   NDJSON so evidence is parseable, not eyeballed. The `#region DEBUG` / `#endregion DEBUG` markers (use the comment syntax of the language) make every probe you added greppable for removal in Phase 2 - nothing gets left behind. Tagging by hypothesis id keeps the ledger and the runtime evidence joined.

5. **Synthesize by differential diagnosis.** Collect each investigator's predicted-vs-actual result into the ledger and set each hypothesis `status` (`verified` / `refuted` / `disputed` / `unverifiable`). Then rank the survivors and pick the **next experiment that is the cheapest one that discriminates between them** - the test whose outcome splits the remaining candidates, not one that merely re-confirms a favorite. Record every predicted-vs-actual delta; a surprise there is often the whole bug.

6. **Tarpit detection - notice when you are stuck.** If investigators keep re-reading the same files, or the new hypotheses are just isomorphic restatements of ones already refuted, you are anchored as a group. Force a perspective break: dispatch one fresh investigator with **zero prior framing** (do not tell it what has been ruled out - let it look cold), or switch to the environment lens ("check the plug") which is where "impossible" bugs usually hide. Thrashing on the same terrain is the signal, not a reason to try the same terrain harder.

When one hypothesis reaches `verified` with evidence and the discriminating experiments have killed its rivals, you have a root cause. Go to Phase 2.

---

## Phase 2 - Fix

You have a confirmed root cause. Now fix it without introducing the next bug.

1. **Failing test first (red).** Write the test that fails *because of this root cause*, and watch it fail. If step 3 of Phase 0 already produced this, good - confirm it is still red against the current tree.

2. **One minimal fix (green).** Change the smallest thing that addresses the root cause and turns the test green. One variable at a time. Resist the urge to refactor the neighborhood while you are in there - that mixes concerns and hides whether your fix was the thing that worked.

3. **Falsify the fix.** This verifies the *test*, not just the patch. Deliberately re-break the code (revert your fix, or inject the fault a second way) and confirm the new test goes red. A test that passes green but never demonstrably catches the bug is theater. Then restore the fix.

4. **Remove all instrumentation.** Grep for `#region DEBUG` and delete every block. This is a checklist item, not a nicety - stray NDJSON probes in shipped code are their own defect. Confirm the grep comes back empty.

5. **Iron laws (do not bend these):**
   - No fix lands without a confirmed root cause. A passing test you never saw fail is not confirmation.
   - One variable at a time - if you change two things and it works, you do not know which one mattered.
   - **3 failed fixes -> stop.** If three genuine attempts have not held, the bug is telling you the architecture or your model of it is wrong. Stop patching and raise it with the user: lay out what you tried, what each attempt predicted, and why each failed. Grinding a fourth patch on a broken mental model wastes everyone's time.

---

## Phase 3 - Verify and record

1. **Original repro passes.** Run the exact pass/fail command from Phase 0. It must now pass.

2. **Full suite, fresh, output read.** Run the whole test suite (not just your one test) from a clean state and actually read the output. Your fix might have broken a neighbor; a green summary line you skimmed is not verification. Read for new failures, new warnings, and skipped tests.

3. **Closer - adversarial verification.** `REQUIRED (if available): adversarial-verify.` If the `adversarial-verify` skill is installed, hand it the ledger and the diff and let it try to break your conclusion - the shared evidence-protocol format means it can audit the ledger directly. If it is not installed, do the inline version: re-read the fix as a hostile reviewer would, asking "what input makes this fix wrong?" and "did I fix the symptom or the cause?" - then test that input.

4. **Auto-autopsy -> `bugs-learned.md`.** Append a short post-mortem to `bugs-learned.md` at the repo root (create it if absent). This is what makes step 2 of Phase 0 pay off next time. Record:
   - **Root cause** - the actual mechanism, one or two sentences.
   - **Bug class** - so future triage can grep by class.
   - **What discriminated** - the single experiment or observation that pinned it. This is the highest-value line; it is the shortcut for next time.
   - **Why it was missed** - what made the wrong hypotheses tempting, so the next reader does not fall for the same bait.

## Definition of done

The pass/fail command is green, the full suite is green from a clean run you read, every `#region DEBUG` block is gone, the fix survived falsification, and `bugs-learned.md` has the autopsy. Anything short of that is "in progress," not "fixed."
