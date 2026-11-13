---
name: learn-ledger
description: "Tutor a person on a topic or on code an agent just wrote, keep what they learned, and schedule spaced review. Use when someone asks to be taught, tutored, drilled or quizzed, or to keep learning while coding with AI. Trigger phrasings: \"teach me X properly\", \"tutor me on\", \"drill me on\", \"quiz me\", \"quiz me on this commit\", \"did I understand this change\", \"what's due for review\", \"review what I learned\", \"update my vault\". Not for a one-off question like \"what is a mutex\" (answer it normally), not for explaining a diff to a reviewer (explain-changes), not for a playable trace of a Python path (microworld), not for auditing an agent's claims (adversarial-verify)."
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: 'for d in "$CLAUDE_PLUGIN_ROOT/skills/learn-ledger" "$CLAUDE_PLUGIN_ROOT/learn-ledger" "$CLAUDE_PROJECT_DIR/.claude/skills/learn-ledger" "$HOME/.claude/skills/learn-ledger"; do if [ -f "$d/scripts/ll.py" ]; then exec python3 "$d/scripts/ll.py" hook witness; fi; done; exit 0'
          timeout: 10
---

# learn-ledger

Teach a person something and make it stick, or keep them learning while an agent writes their code.
You run the tutoring in this conversation, and `ll.py` records every graded exchange and computes levels, the review schedule and the Obsidian view from that record.
It costs the learner time on purpose. Say so once if they seem surprised.

In every command below, `LL` means `python3 "${CLAUDE_SKILL_DIR}/scripts/ll.py"`.

## Non-negotiables (re-read after compaction)

1. **Status first.** Run `LL status` at every invocation, and again after compaction or a resume before doing anything else. It restores the open question, the current node, levels and the due count from disk. If this is the first use, run `LL init` (add `--vault PATH` if the learner wants Obsidian).
2. **Seal before you ask.** Every graded question goes through `LL seal`, `LL pose`, then your message ends at the question. When the learner replies, `LL answer QID --from-witness`, then `LL reveal QID`, then grade. `ll.py` refuses out-of-order calls. Never pose a question you did not seal, and never write the answer, a hint or options after the question. Ask in plain text, never through AskUserQuestion, since only a typed reply is witnessed.
3. **Never retype the learner's answer.** The witness hook captured what they typed. If `--from-witness` lists several prompts, pick the learner's answer with `--witness ID`. If it says no prompt was witnessed (hooks lost after a resume), re-invoke `/learn-ledger`, ask them to resend, or use `--text`, which earns nothing until `LL verify` finds it in the transcript.
4. **The script owns mastery.** Never state a level, "mastered", "you've got this down" or any progress claim that `LL levels` did not print. Praise or correct the answer, never the person's level.
5. **A miss gets one hint rung, not the answer.** Climb one rung per request (pedagogy reference), from the first broken step in their reasoning. Reveal the answer only on "just tell me" (rung R5) or after R4. Log each retry with another `LL answer`, then grade the last one. The script counts the rungs from the retries.
6. **No leaks before reveal.** In check mode never read `sealed/` before `LL reveal`. Run no background subagent while a question is open, since its report would arrive as a prompt.
7. **Run, do not predict.** Any statement of what example code prints comes from running it. Any code you show from a repo file comes from `LL snippet FILE:START-END`, never retyped.
8. **Intent guard.** A one-off question ("what is a mutex", "how do I use X") gets a normal answer and no loop. If intent is unclear, ask once, "quick answer, or teach it properly?"
9. **Never nag, never block.** No offer unless the commit hook asked for one, at most one sentence, and a "no" ends it for the session. Never edit settings or block git.

## Question kinds (Bloom)

| Kind | Bloom | The learner must | Sealed with |
|---|---|---|---|
| K1 | remember | recall the idea from a cue that does not contain it | answer |
| K2 | understand | explain why, or predict an outcome | answer, wrong models |
| K3 | apply | use it on a case not seen in teaching | answer, wrong models |
| K4 | analyze | find the flaw in a plausible wrong claim, or pick between near-twins whose wrong options are named wrong models | answer, wrong models (required) |
| K5 | evaluate and create | handle an edge case and teach it back | rubric of must-criteria, every one must be met |
| predict | none | guess before a step is taught | answer, never counts toward levels |

A level L needs kinds K1 to L each passed twice, on different questions and different days, witnessed, at rung R2 or below, with K1 cold (nothing on that node taught or revealed earlier in the session). A miss resets that kind. You never compute this. `LL levels` does.

Seal packet, one object or a list on stdin to `LL seal --node N --kind K`:

```json
{"question": "...", "answer": "...", "wrong_models": ["the specific wrong belief, and the answer it produces"], "citations": ["file:line"], "rubric": ["must-criterion"]}
```

Build wrong options from specific wrong models the learner might hold, never filler. Ask for confidence in the same line ("answer, then @0-100 for how sure you are"), and accept `idk` or `?` as a valid don't-know.

## teach

1. `LL status`, then `LL distill-input --topic T` to see the propositions already held, so you do not re-probe them.
2. Make the goal concrete with one or two questions, not a lecture.
3. Probe. Name the strands the goal depends on and bracket each one's floor and ceiling by binary search, entering near the top. Every probe question is sealed and graded. Stop when every strand is bracketed, or after about 8 questions for a narrow topic.
4. Plan the minimal dependency tree from what is held to the goal. Record nodes with `LL node add --topic T --id N --title S --parents A,B` and show the plan as a coarse ASCII map.
5. Per reasoning step, optionally a sealed `predict` question, then teach one step and log it with `LL teach --node N --file STEP.md` (the step as you taught it, the distiller's input), then one sealed check of the kind the step targets, then repair or continue.
6. Close with retests of every miss and every item that needed rung R3 or more, each on a fresh surface (new numbers, new context, same idea). Then dispatch the distiller (`agents/distiller.md`) with the topic and the `ll.py` path, print `LL levels`, and run `LL export` if a vault is set.

## review

`LL due` prints the ordered, interleaved queue. For each item write a fresh question from that node's propositions, of that item's kind, seal it, pose it. Follow the queue order. If `due` says single node, vary the surface instead of interleaving. Close as teach does.

## check (learning while coding with AI)

1. Resolve the range (default, from the last check that `LL status` names to `HEAD`, else `HEAD~1..HEAD`) and size it with `git diff --stat`. Trivial or docs-only changes get 0 questions, small 1, medium 2, large 3.
2. Dispatch the examiner (`agents/examiner.md`) in the foreground with the range, the repo path, the path `${CLAUDE_SKILL_DIR}/scripts/ll.py` and the question count only. Never pass it the chat, your intent, or an explain-changes brief.
3. It seals each question plus one backup scenario and returns only qids and question text. Pose each in turn.
4. Grade after reveal. A miss climbs the hint ladder as rule 5 says, and if it still ends in a miss, pose the sealed backup scenario on the same concept, never the same question reworded.
5. Open book. The learner may read the code. Point to `file:line` rather than pasting, and anything shown comes from `LL snippet`.

If the learner wants to write code themselves during a task, recommend the built-in Learning output style (`/output-style Learning`), which leaves `TODO(human)` spots at real design decisions. Their code lands in the next diff, so check mode quizzes it.

## Learner commands, any time

`progress` (run `LL levels`), `harder`, `easier`, `just tell me` (reveal, rung R5), `skip` (answer `idk`, a don't-know), `dispute` (`LL dispute QID --reason S`, which drops the grade), `pause` (stop the loop, state stays on disk).

## Boundaries

- To watch a Python path actually run, hand off to microworld. Never simulate a real code path in an Artifact. Use an Artifact only for a concept that is dynamic on its own (a state machine stepping, a curve under a parameter), never as storage.
- What you taught can be wrong. `LL ledger --topic T` renders it as `L` assertion rows that adversarial-verify can audit.

## Setup, once, on request

- `LL hook install --print` prints settings hooks for post-commit offers and a due reminder. Show the output and let the learner add it. When an offer arrives, follow its instructions exactly, then `LL offer accept --rev SHA` or `LL offer decline --rev SHA`.
- `LL optin --pause 7d`, `--off` or `--on` controls offers.
- Tell the learner once that Claude Code prompt suggestions can pre-fill an answer, and that `promptSuggestionEnabled: false` in settings turns them off.

If an agent type is unavailable, dispatch a general-purpose subagent with the agent file's text inline.

## References

- [references/pedagogy.md](references/pedagogy.md) for the probe, the step cycle, the hint ladder, practice modes and reading confidence.
