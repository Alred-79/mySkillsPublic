# Spec: learn-ledger

Status: built 2026-11-13. Skill, `ll.py`, script tests (59 passing) and eval fixtures are in `learn-ledger/`, one sonnet smoke run of `teach-closures` passed every mechanical row, and the full with-skill and baseline benchmark has not been run. Designed 2026-11-13 from a brief plus one prior adversarial review, whose findings are folded in as constraints.
Adversarially reviewed 2026-11-13 against the hooks, skills and subagents docs, a local hook experiment on Claude Code 2.1.322, and the cited papers; all 17 findings resolved in this revision, with dated notes where the design moved.
Depends on: [evidence-protocol.md](evidence-protocol.md)
Siblings: [microworld.md](microworld.md) (deep trace-grounded tier it hands off to), [explain-changes.md](explain-changes.md) (tells a reviewer about a change, where this skill tests the human on it), [adversarial-verify.md](adversarial-verify.md) (audits what this skill taught).
Name checked 2026-11-13. `npx skills find learn-ledger` and a GitHub code search for `"name: learn-ledger"` returned no such skill, and `learn`, `keep-learning` and `understudy` are taken.

## Purpose

Two jobs, one record.
Teach a topic properly and keep it, and keep a person learning while an agent writes their code, instead of watching it work.
The skill runs the tutoring in the main conversation and records every graded exchange in an append-only event log on disk.
A stdlib script, never the model, turns that log into levels, a review schedule, and an Obsidian view.
The model asks, teaches and grades against an answer it sealed before asking, and the learner's answer is captured by the harness, not retyped by the model.
It costs the learner time on purpose, and says so.

## The delta-only rule

A frontier model asked to "teach me X" or "quiz me on this commit" already explains well, asks reasonable questions, and praises.
What it does not do unprompted, and what this skill encodes, is five mechanisms a prompt alone cannot provide.

1. **Evidence-derived levels.** Levels 0 to 5 are computed by a script from logged, graded, witnessed events, so the model can never declare mastery.
2. **Committed answers.** Every graded question has its reference answer, wrong-model map, or rubric sealed to disk with a hash before the learner sees the question, so grading cannot drift toward whatever the learner said.
3. **Witnessed answers.** A skill-scoped `UserPromptSubmit` hook records what the human actually typed, so a logged answer the human never gave cannot earn credit.
4. **A context-isolated examiner.** In coding mode the questions come from a subagent that sees only the diff and the repo, never the chat, so they test what the code does rather than what the agent said it meant.
5. **Durable cross-session state with spaced review.** The schedule is derived from the event log, survives compaction and new sessions, and is restored by one `status` call.

Everything else in the skill is short doctrine that keeps those five honest.

## Market position (researched 2026-11)

| Source | What it has | What it lacks |
|---|---|---|
| LearnHarness (amosblomqvist/learnharness, AGPL-3.0, about 9.1k stars, pushed 2026-11-12) | The strongest doctrine found. Probe that brackets floor and ceiling per strand, minimal dependency tree, predict then teach then check per reasoning step, confidence read against correctness, practice modes, hint ladder R0 to R5, commit the model solution before posing, propositions and jointly-implying chains with provenance | It is a desktop app. Its only skill is a read-only reader of the app's data. Its practice doctrine explicitly has no level outputs and no state record. AGPL, so only ideas transfer, never wording |
| Jane Street socratic-tutor (MIT) | Intent guard, 0 to 5 map rendered as ASCII, one question per message, strict level rule of 2+ independent checks with one unprompted recall, final mixed assessment, user commands | Levels are judged by the model in its own context. State persists only as a block the user pastes. Spaced review has no schedule |
| learning-opportunities (DrCatHicks, CC-BY-4.0, about 2.6k stars) | End the message at the question, fading scaffolding, max 2 offers per session and none after a decline, a `PostToolUse` hook on `git commit` | No grading, no record. The hook keeps its counter in a temp file and leaves decline tracking to the model |
| Sphinx (parthh01/sphinx, MIT, about 500 stars) | Examiner in a separate context that sees only the committed change, questions on behavior, failure modes and invariants, open book, a fresh scenario after a miss | A Node app that blocks `git push` for up to 25 minutes and calls its own reviewer model. No learning record and no spacing. It says itself that passing proves nothing about unaided understanding |
| learn-codebase (ktaletsk, MIT, about 100 stars) | One useful operational fact. Claude Code prompt suggestions can pre-fill an answer before the learner reasons | The journal and its three mastery labels are written by the model. The brief's claim that it tracks confidence separately from correctness did not hold up on reading the source, so it is not a source for confidence |
| Claude Code Learning output style (built in) | `TODO(human)` handoffs at real design decisions | Nothing is checked or recorded. It applies to every response and cannot be rate limited |

The intersection nobody occupies is a skill plus a stdlib script where levels come from witnessed, sealed, graded events and spaced review is derived from the same log.

**The problem is real, with honest sizes.**
Shen and Tamkin (Anthropic, arXiv 2601.20245, n=52, 26 per arm) found a 17% quiz score difference, about 2 grade points, against the AI arm, with the largest gap on debugging questions.
Their low-scoring interaction patterns (AI delegation, progressive reliance, iterative AI debugging) averaged 24% to 39%, and the high-scoring ones (generation then comprehension, hybrid code explanation, conceptual inquiry) averaged 65% to 86%, but each cluster had only 2 to 7 people.
Bastani et al. (PNAS 2025, 122(26) e2422633122, about 1,000 students) found unguarded GPT access raised practice grades 48% but cut later exam grades by 17%, and a guarded tutor largely removed the harm.
Kazemitabaar et al. (arXiv 2410.08922) is weaker than the brief said.
Lead-and-Reveal scored 58.3 against a 31.5 baseline in study 1 (p=.058, not significant), showed no post-test difference in study 2, took about 1.8 times as long, and its one significant result was better agreement between self-assessed and actual ability.
Cepeda et al. (Psychological Science 2008, over 1,350 people) found the optimal review gap grows with the retention interval, from about 20 to 40% of a one-week delay to about 5 to 10% of a one-year delay, which motivates an expanding interval rather than a fixed one.

## Boundaries with the pack

| | learn-ledger | microworld | explain-changes | adversarial-verify |
|---|---|---|---|---|
| Job | Build and keep the human's understanding, measured over time | Let the human inhabit one Python path's real runtime behavior | Tell a reviewer what a change does | Refute an agent's claims |
| Output | Questions, a durable event log, levels, a schedule | A playable trace-backed artifact | A terse grounded brief | A verdict and findings |
| Who is tested | The human | The human, once, with no mastery verdict | Nobody | The agent |

Rules, written into the descriptions.
When the learner wants to watch a Python path actually run, hand off to microworld and do not simulate behavior in an Artifact.
A microworld quiz result is not imported as a level, which honors microworld's no-mastery-verdict rule, though its mechanism can be scheduled for review here afterward.
"Explain this diff" routes to explain-changes, and "quiz me on this diff" routes here.
The examiner reuses explain-changes's grounding discipline (every committed answer cites a hunk or `file:line`) but never reads an explain-changes brief, since that would be the agent's narration again.
learn-ledger never audits itself.
It emits what it taught as `L` assertion rows, and adversarial-verify audits them on request or when the learner disputes an answer.
For hands-on writing during a task, recommend the built-in Learning output style rather than reimplementing `TODO(human)`.
Code the learner writes there lands in the next diff, so check mode quizzes it for free.

## Files

```
learn-ledger/
  SKILL.md                  # modes, non-negotiables, commands. Target 3,500 tokens, hard cap 5,000
  references/pedagogy.md    # probe, step cycle, question kinds, hint ladder, practice modes, confidence reading
  references/ledger.md      # event schema, level and review rules, export layout, for humans and the builder
  agents/examiner.md        # check-mode question writer (Read, Grep, Glob, Bash for git and ll.py only)
  agents/distiller.md       # turns logged teach steps into propositions and chains
  scripts/ll.py             # stdlib Python 3.10+, the only writer of the store
  evals/                    # layout per evidence-protocol.md, plus scripts/tests for ll.py
```

Portability rule, as in adversarial-verify.
If an agent type is unavailable, dispatch a general-purpose subagent with the agent file's text inline.
The non-negotiables sit in the first 1,500 tokens of SKILL.md so they survive compaction, which keeps only the first 5,000 tokens of a skill.

## Modes and triggers

| Mode | Triggers | Rate limit |
|---|---|---|
| `teach <topic>` | Explicit only. "teach me X properly", "tutor me", "drill me on X", `/learn-ledger teach X` | None, the learner asked |
| `review` | "quiz me", "review what I learned", "what's due", or accepting a due reminder | None when asked |
| `check [range]` | "quiz me on this commit", "did I understand this change", or accepting a post-commit offer | Offers only, below |
| `status` | Any invocation runs it first, and the model runs it after compaction or resume | None |
| `export` | "update my vault", and automatically at the end of a session when a vault path is set | None |

**Intent guard.** A one-off question ("what is a mutex", "how do I use X") gets a normal answer and no loop.
If intent is ambiguous, ask one short question ("quick answer, or teach it properly?") before probing.

**Post-commit offer (opt-in).** `ll.py hook install --print` prints a `PostToolUse` hook on `Bash` for the user to add to their settings, and the skill never edits settings itself.
The printed hook filters with `if: "Bash(git commit *)"`, and the command `ll.py hook post-commit` reads the hook JSON and stays silent unless all of these hold.
The input has no `agent_id`, since settings hooks also fire inside subagents, which cannot ask the learner (review note 2026-11-13).
The command matches `git commit` and `tool_response.stdout` shows a created commit, since `PostToolUse` fires only on success and carries no exit code.
The commit changes at least `min_changed_lines` (default 15) lines outside docs, tests, lockfiles and generated paths.
No offer was logged in this session, fewer than `max_offers_per_day` (default 3) were logged today, and no `seal` event carries this repo and SHA.
No decline was logged in this session, and the last two offers were not both declined within the past 72 hours.
No `pause` is active (`ll.py optin --pause 7d` or `--off`).
When all hold it logs an `offer` event and returns `additionalContext` telling the model to finish the user's current request first, then ask one short sentence, then wait.
A yes runs `ll.py offer accept` and then check mode, and a no runs `ll.py offer decline`.
All limits are computed from the event log, so they hold across sessions, unlike a temp-file counter.

**Due reminder (opt-in, off by default).** A `SessionStart` hook with source `startup` emits one line as a `systemMessage`, which the user sees and the model is not told to act on, only when at least 3 items are due and no reminder was logged today.
Plain stdout would land in the model's context and pull it toward reviews during an unrelated first task (review note 2026-11-13).

**No output style and no Stop hook.** An output style applies to every response and cannot be rate limited.
A blocking Stop hook stalls every turn that waits on the learner, a finding from the prior review.

**Learner commands, any time.** `progress`, `harder`, `easier`, `just tell me` (reveal this question, logged as rung R5), `skip` (logged as don't-know), `dispute` (voids the grade and logs a dispute), `pause`.

## Workflow

Every graded question follows one gated sequence, enforced by `ll.py` refusing out-of-order calls.

```
seal (answer, wrong models or rubric, hash) -> pose (question shown, message ends) -> learner replies
-> answer --from-witness -> reveal (hash rechecked) -> [hint rung -> learner replies -> answer]* -> grade -> next
```

A qid may take several `answer` events after its reveal, one per hint rung, and `grade` grades the last one with `hint_max` at least the highest rung given.
The earlier draft allowed one answer per qid, which left no legal path for the hint ladder (review note 2026-11-13).

**Teach.**
1. `status`, then read the topic's existing propositions so held strands are not re-probed.
2. Make the goal concrete with questions, not a lecture.
3. Probe. Name the strands the goal depends on and bracket each one's floor and ceiling by binary search, entering near the top. Every probe question is sealed and graded, and probing stops when every strand is bracketed or after about 8 questions for a narrow topic.
4. Plan the minimal dependency tree from what is held to the goal, record nodes with `ll.py node add`, and show it as a coarse ASCII map.
5. Per reasoning step, an optional prediction (sealed, kind `predict`, never counted toward levels), then one step taught and logged with `ll.py teach`, then one check of the targeted kind, then repair or continue. Any claim about what example code prints comes from running it, never from the model's prediction.
6. On a miss, no answer. One hint rung per request, from the first broken step in the learner's reasoning.
7. Close with retests of every miss and every item that needed rung R3 or more, each in a fresh surface. Then dispatch the distiller, print `levels`, and run `export` if a vault is set.

**Review.**
`ll.py due` returns the ordered, interleaved queue.
The main thread writes a fresh question for each item from that item's propositions, seals it, and poses it.
Same close as teach.

**Check.**
1. Resolve the range (default, commits since the last check for this repo, else `HEAD~1..HEAD`) and size it. Trivial or docs-only changes get 0 questions, small changes 1, medium 2, large 3.
2. Dispatch the examiner with the range and repo path only.
3. The examiner returns a packet sealed through `ll.py seal`, where each question carries a scenario, its kind, a committed answer citing `file:line`, 2 or 3 wrong models, and one sealed backup scenario on the same concept.
4. The main thread poses each question. A miss gets the reveal and then the backup scenario, never the same question reworded.
5. Open book. The learner may read the code. Point to `file:line` rather than pasting, and any code that is shown comes from `ll.py snippet`, never retyped.

**Main thread or subagent.**

| Step | Where | Why |
|---|---|---|
| Probe, teach, pose, grade, hints | Main | Turn-taking with the learner, and subagents cannot use `AskUserQuestion` |
| Check-mode question writing | Examiner subagent | The main thread wrote the code and is anchored on its intent. The examiner sees the diff and the repo but never the chat, and a canary eval proves it |
| Distill | Distiller subagent | Its input is entirely on disk (logged teach steps), it needs no learner, and it keeps the main context small after a long session |
| Review question writing | Main | Reads propositions from disk, and a subagent round trip per item adds latency for no decorrelation gain |
| Grading | Main | A per-turn subagent adds latency, while the seal already fixes the reference and dispute plus adversarial-verify catch a wrong key |

`AskUserQuestion` is used only for the intent guard and setup choices.
Graded questions are plain messages that end at the question, so answers arrive as typed prompts the witness hook captures, confidence fits in the same line, and the tool's own guidance (use it only for genuine decisions) is respected.

## Commit-before-ask and the witness

**Seal.** `ll.py seal` writes `sealed/<qid>.json` (question, reference answer or rubric, wrong models, citations) and appends a `seal` event with the SHA-256 of that file.
The event was called `commit` in the draft and was renamed so it cannot be confused with a git commit in the offer limits (review note 2026-11-13).
`pose` refuses a `qid` without a `seal` event, `reveal` refuses before an `answer` event and rechecks the hash, and `grade` refuses unless the order is seal, pose, answer, reveal.
It guarantees the reference existed, unchanged, before the learner saw the question, so the key cannot be rewritten to fit the answer.
In check mode `seal` prints only qids and question text, and the main thread is instructed not to read `sealed/` before reveal, so it does not see the examiner's key early, though nothing but that instruction stops it.
It does not guarantee the key is correct (dispute and adversarial-verify cover that), it does not stop lenient grading against a correct key, and a model that skips the script entirely produces no credit rather than false credit.

**Witness.** SKILL.md declares a skill-scoped `UserPromptSubmit` hook (`ll.py hook witness`), registered when the skill is invoked and kept for the rest of that Claude Code process.
While a question is posed and ungraded in that session, it appends the prompt's text, `session_id` and timestamp to `witness.jsonl`, and otherwise it writes nothing, so unrelated prompts never reach the store.
`ll.py answer QID --from-witness` takes the latest witnessed prompt in the same session after the pose, so the model never transcribes the learner's answer.
If more than one prompt was witnessed since the pose, it lists them and requires `--witness ID`, and the text is still copied from the record.
Review notes 2026-11-13, each from the hooks docs or a local experiment on Claude Code 2.1.322.
The draft took the first prompt after the pose, but a learner's clarifying question comes first, and `UserPromptSubmit` also fires for background subagent reports, scheduled tasks and cross-session messages, so no background subagent runs while a question is open.
`${CLAUDE_SKILL_DIR}` is not substituted in frontmatter hook commands, so the hook command finds `ll.py` by probing `$CLAUDE_PLUGIN_ROOT`, `$CLAUDE_PROJECT_DIR/.claude/skills/learn-ledger` and `~/.claude/skills/learn-ledger`, and exits 0 silently if none exists, so it never blocks a prompt.
The hook never records a slash command, since a live build run credited the `/learn-ledger status` invocation itself as the learner's answer.
Skill hooks do not survive `--resume` or a restart (a second `-p --resume` turn fired nothing, while a second turn in the same process did), so after a resume the model re-invokes the skill before posing, and `answer --from-witness` with no record since the pose fails with that instruction rather than guessing.
Confidence is parsed from a trailing `@NN` (percent sure), `idk` or a lone `?` means don't-know with no confidence, and a missing confidence is null, never zero.
**Fallback transcript check.** If no witness exists (hooks disabled by policy, say), `answer --text` is accepted but marked `pending`, and `ll.py verify` later looks for that text as a user message in `~/.claude/projects/<project-slug>/<session>.jsonl` after the pose time.
Found means `witnessed`, and absent or unparseable means `unwitnessed`.
Only witnessed answers earn level credit.
It guarantees the credited answer was typed by the human in that session.
It does not guarantee unaided understanding, since the learner may have asked an agent or a search engine, which open book permits and `status` says in its footer.
The transcript format is internal and undocumented, so the fallback fails closed, and the transcript is written asynchronously, so `verify` runs lazily from `status` and `levels`.

## Data model

Store at `~/.learn-ledger/` (override with `LEARN_LEDGER_HOME`), because learning belongs to the person across repos, and check-mode events carry the repo and commit SHA.
The `session` field comes from `CLAUDE_CODE_SESSION_ID`, which Claude Code sets in Bash and hook subprocesses.

```
~/.learn-ledger/
  config.json         # vault_path, rate limits, ladder, thresholds
  events.jsonl        # append-only source of truth, fcntl-locked appends
  sealed/<qid>.json   # committed packets, hashed in their seal event
  witness.jsonl       # prompts captured by the skill-scoped hook
  propositions.jsonl  # append-only assertions, merged on read
  chains.jsonl        # premises jointly imply a conclusion, merged on read
```

**Event.** Every line has `v`, `id` (time-ordered), `ts` (ISO with offset), `day` (local date), `session`, `mode`, `type`, plus type fields.

| `type` | Fields |
|---|---|
| `node` | `node`, `topic`, `title`, `parents` |
| `teach` | `node`, `text` (the step as taught, the distiller's durable input), `props` |
| `seal` | `qid`, `node`, `kind`, `sha256`, `prompt_hash`, `repo`, `rev` |
| `pose` | `qid` |
| `answer` | `qid`, `text`, `confidence`, `dont_know`, `witness` (`hook`, `pending`, `witnessed`, `unwitnessed`), one per hint rung |
| `verify` | `qid`, `answer`, `witness`, settling a pending `--text` answer from the transcript |
| `reveal` | `qid`, `hash_ok` |
| `grade` | `qid`, `verdict` (`pass`, `partial`, `fail`), `miss_class` (`cue`, `discrimination`, `execution`, `careless`, `structural`), `wrong_model`, `hint_max` (0 to 5) |
| `dispute` | `qid`, `reason` |
| `offer`, `accept`, `decline`, `pause`, `reminder` | `repo`, `rev` or `until`, with `accept` and `decline` from `ll.py offer` |
| `distilled` | `teach_ids`, `props`, `chains` |

**Question kinds (Bloom).**
K1 remember, recall the idea from a cue that does not contain it.
K2 understand, explain why or predict an outcome.
K3 apply, use it on a case not seen in teaching.
K4 analyze, find the flaw in a plausible wrong claim or pick between near-twins whose wrong options are named wrong models.
K5 evaluate and create, an edge case plus a teach-back graded against a sealed rubric, where every must-criterion has to be met.
`predict` is ungraded toward levels.

**Level rule** (`ll.py levels`, per node).
1. An attempt is a `seal`, `pose`, `answer`, `grade` chain for one `qid` in valid order, judged on its last answer. Disputed attempts are dropped.
2. An attempt is *cold* when no `teach` event on its node and no `reveal` of another question on its node occurred earlier in the same session.
3. An attempt *qualifies* for kind k when its verdict is `pass`, its answer is `witnessed` or `hook`, it is not don't-know, `hint_max` is at most 2, and, for K1 only, it is cold.
4. For each kind k, take the attempts after the most recent non-passing attempt of kind k (fail, partial or don't-know), witnessed or not, since a miss is evidence whoever typed it. Kind k is *met* when at least 2 of those qualify, on distinct `prompt_hash` values, spanning at least 2 distinct local days.
5. `level = max L in 0..5 such that kinds 1..L are all met`, else 0.
6. Levels are printed by `levels`, `status` and `_progress.md` only, and never written into a proposition note or stated by the model on its own authority.

**Review rule** (`ll.py due`).
1. An item is a pair (node, k) with at least one qualifying pass.
2. Walk the item's attempts in time order with `n = 0` and no anchor day yet. `LADDER = [1, 3, 7, 16, 35, 75]` days, configurable, and `interval(n) = LADDER[min(n, 5)]`.
3. Any attempt that is not a qualifying pass (a fail, partial, don't-know, or a pass needing rung R3 or more or left unwitnessed) sets `n = 0` and the anchor to its day.
4. A qualifying pass with no anchor yet, or at least `ceil(interval(n) / 2)` days after the anchor, raises `n` by one and moves the anchor to its day. An earlier one is logged but changes nothing, so cramming cannot game the schedule.
5. `due_day = anchor + interval(n)`, and the item is due when `today >= due_day`.
The draft counted passes against an interval that itself depended on the count, and let a heavily hinted pass push the next review out by a full interval (review note 2026-11-13).
6. Weakest first is a sort on, in order, last verdict non-passing, lower `n`, lower k, more chains using the node as a premise, older last attempt.
7. Take up to `review_size` (default 8) and interleave greedily, each next item the weakest whose node differs from the previous one, else the weakest left, since one dominant node can make full interleaving impossible.
8. Too few to interleave. If the due items span fewer than 2 nodes, pad with not-yet-due items from other nodes, nearest `due_day` first. If the store has only one node, run it without interleaving, vary the surface instead, and say so.

**Propositions and chains.** One line per assertion with `id`, `topic`, `statement`, `aliases`, `source` (URL with access date, `file:line@rev`, or `model-asserted`), and `provenance` (event ids).
Chains carry `premises` (all used together), `conclusion`, and `provenance`.
Merging follows LearnHarness's documented rule (first line for an id defines it, provenance unions), restated in our own words.
**Dedup.** `ll.py prop similar "<statement>"` returns existing statements above a normalized token-overlap threshold (default 0.8), and the distiller must merge into an existing id or explain why the new one differs.

**`L` assertion rows.** `ll.py ledger --topic T` renders propositions and the committed answers of revealed check-mode questions in the evidence-protocol table, never an unrevealed key such as an unused backup scenario.
A cited `file:line@rev` verified by `snippet` is `verified`, `model-asserted` is `unverifiable`, a disputed one is `disputed`, and version-sensitive facts carry an `expiry`.
This is the packet adversarial-verify audits.

**Obsidian export** (`ll.py export`).
The vault path comes from `config.json` or `--vault`, with no default, and export writes only under `<vault>/learn-ledger/`, which it regenerates wholesale.

```
<vault>/learn-ledger/
  README.md                   # generated view, edits are overwritten, source is ~/.learn-ledger
  _progress.md                # ASCII level map and due queue, the only place levels appear
  topics/<topic>.md           # map of content, links to its propositions
  propositions/<id>-<slug>.md # statement, source, provenance, body link "premise of [[<cid>]]"
  chains/<cid>.md             # premises as plain text, body "jointly imply [[<id>-<slug>]]" for the conclusion
```

Graph view drops direction, so direction lives in who links whom.
A premise note links to its chain, the chain links only to its conclusion, and a conclusion does not link back, leaving the backlinks pane to show it.
Every wikilink names the target's full file basename, since `[[p1]]` does not resolve to `p1-slug.md`.
The draft's chain template linked its premises too, which made the graph bidirectional (review note 2026-11-13).
Links sit in note bodies, and any in frontmatter are quoted per Obsidian's property syntax.

**Artifacts.** Optional, only for a concept that is dynamic (a state machine stepping, a curve changing with a parameter), never as storage, and never to simulate a real code path's behavior, which goes to microworld.

## Scripts

```
ll.py init [--vault PATH]                     # create the store and config
ll.py status                                  # restore after compaction: open question, current node, levels, due count
ll.py node add --topic T --id N --title S [--parents A,B]
ll.py teach --node N --file STEP.md [--props P1,P2]
ll.py seal --node N --kind K < packet.json    # many packets accepted, prints qids and question text only
ll.py pose QID
ll.py answer QID (--from-witness [--witness W] | --text S)
ll.py reveal QID
ll.py grade QID --verdict V [--miss-class C] [--wrong-model W] [--hint-max R]
ll.py dispute QID --reason S
ll.py levels [--topic T]                      # ASCII map, runs verify first
ll.py due [--size 8]
ll.py verify                                  # transcript fallback for pending answers
ll.py prop add|similar ...  ll.py chain add ...  ll.py distill-input
ll.py snippet FILE:START-END [--rev R]        # verbatim lines plus a content hash
ll.py ledger --topic T
ll.py export [--vault PATH]
ll.py optin (--pause 7d | --off | --on)
ll.py offer (accept | decline) [--rev R]
ll.py hook (witness | post-commit | session-start | install --print)
```

`ll.py` has unit tests under `evals/scripts/` that run without a model.

## What was kept and cut

Overlaps were resolved toward the stronger source.

| Cut | Why |
|---|---|
| Jane Street's "explain after 2 or 3 failed attempts" | LearnHarness's one-rung-per-request ladder is more precise and reveals less |
| Jane Street's devil's advocate on right answers | K4 (find the flaw) does the same work and is graded and logged |
| Jane Street's save-state and resume-from paste block | The store on disk plus `status` supersedes it |
| learning-opportunities' fixed 2 offers per session | Replaced by stricter durable limits (1 per session, 3 per day, a decline silences the session, two declines back off 72 hours) |
| learning-opportunities' "end the message at the question" as a separate rule | Identical to Jane Street's one-question rule, so kept once |
| A Lead-and-Reveal coding mode | Its learning gain was not significant and it cost about 1.8 times the time. Check mode implements generation then comprehension, the pattern Shen and Tamkin saw score highest, and the Learning output style already covers writing it yourself |
| Sphinx's blocking push gate, distance setting and own model routing | Blocking git is a nag, distance is covered by question kinds, and Claude Code's own subagent replaces a reviewer API |
| learn-codebase's model-written journal and fixed 1/3/7/14 ladder | The script derives both from events |
| A Stop hook and a shipped output style | Stalls learner turns, and cannot be rate limited |
| A grading subagent per answer | Latency per turn for little gain once the key is sealed |
| `AskUserQuestion` for graded questions | No confidence field, answers bypass the prompt witness, and its own guidance reserves it for genuine decisions |

Kept from the Neo4j graph engineering slide, as framing rather than new machinery.
The gated seal, pose, answer, reveal, grade sequence is a small procedure graph with declared inputs and refusals.
Propositions and chains with provenance are the context graph.

## Evals and testing plan

Artifacts in `evals/`, shared rules in [evidence-protocol.md](evidence-protocol.md) (evals first, uplift against a baseline, 3 or more reps, 2 model tiers, trigger evals separate).

**Script tests (deterministic, must be 100%).** Forged event logs under `evals/fixtures/logs/` assert that two passes on the same day do not meet a kind, a pass at `hint_max` 3 does not qualify, an unwitnessed pass does not qualify, a warm K1 pass does not qualify, a fail resets its kind, a disputed attempt is dropped, `grade` refuses a seal logged after its answer, `reveal` detects an edited sealed file, `due` reproduces a hand-computed queue including the too-few-to-interleave case, every post-commit rate limit fires, and `export` writes the documented layout with no level in any proposition note.

**Simulated learner.** Multi-turn evals pair the skill session with a simulator subagent driven by a profile in `evals/fixtures/learners/`.
A profile fixes what the learner knows, one seeded misconception with its exact wrong answer, confidence values, and a scripted `just tell me` and `skip`.
The simulator sees only the assistant's messages, and its replies pass through the real witness hook, so each case runs as one `claude -p --input-format stream-json` process, since skill hooks do not survive `--resume`.

**Fixtures and cases.**
1. `teach-closures`. Topic, Python closures and default arguments, for a learner who holds the misconception that default values are re-evaluated on every call.
2. `check-queue`. A tiny repo whose last commit adds a job worker that commits its side effect before acknowledging the job. The chat history carries a canary sentence ("we chose ack-after-commit for latency") that must not reach the examiner. The learner misses the duplicate-on-redelivery question once.
3. `review-due`. A seeded store with 5 nodes, one failed yesterday, two due, two not due, plus a single-node variant.
4. `one-off`. "what's a mutex?" with the skill installed.
5. `nag`. Two qualifying commits in one session after a decline, then a docs-only commit.

**Scored behaviors.**

| Behavior | Type |
|---|---|
| A `seal` event precedes every graded `pose`, read from the store | Hard fail, pass^k |
| No answer is credited unless it matches what the simulator actually sent | Hard fail, pass^k |
| The model never states a level or "mastered" that `ll.py levels` does not print | Hard fail, pass^k |
| The canary sentence is absent from the examiner's Agent prompt, read from the transcript | Hard fail, pass^k |
| Every code block attributed to a repo file is a verbatim substring of that file at that rev | Hard fail, pass^k |
| Every stated output of example code matches an actual run of it | Hard fail, pass^k |
| One question per message, and the message ends at the question | Scored |
| The probe surfaces the seeded misconception and a wrong model names it | Scored |
| A miss gets one hint rung, not the answer, unless the learner asks | Scored |
| Check questions concern behavior, failure modes or invariants, not names (judged) | Scored |
| A miss in check mode gets the sealed backup scenario | Scored |
| Review order and interleaving match `ll.py due` | Scored |
| Every miss is retested in a fresh surface before close | Scored |
| `one-off` gets a plain answer with no loop, and `nag` gets no second offer and no docs offer | Scored |

**Baseline.** The same prompts and the same simulator with the skill absent.
Expected baseline failures are several questions or a hint in one message, no sealed key, praise that implies mastery, nothing persisted, questions on identifiers, the same question reworded after a miss, and no schedule.
Mechanism rows that a baseline cannot satisfy by construction (store-based checks) are scored as behavior proxies on the baseline, such as whether a reference answer was stated before the learner replied.

**Thresholds.** Script tests 100%.
Hard fails hold on every rep.
With-skill mean on scored behaviors at least 0.85, and uplift over baseline at least 0.30.
Rows passing 100% in both arms are pruned while the seed is kept.
Judged rows use swapped order and anonymized provenance per the shared rules.

**Trigger evals.** About 20 queries, 3 runs each, 60/40 split.
Should trigger, "teach me Raft properly", "drill me on SQL joins", "quiz me on the commit I just made", "what's due for review".
Should not trigger, "what is a mutex", "explain this diff" (explain-changes), "build an interactive explainer for this parser" (microworld), "verify this answer" (adversarial-verify).
Pass at least 0.8 on should-trigger and at most 0.2 false triggers.

**Honest ceiling.** These evals measure protocol fidelity against simulated learners, not human learning.
A human study is future work.

## Assumptions

| Assumption | Status |
|---|---|
| After compaction Claude Code re-attaches the first 5,000 tokens of each invoked skill, within a 25,000 token shared budget | Confirmed, Claude Code skills docs |
| Subagents cannot use `AskUserQuestion`, and do not see the parent conversation | Confirmed, sub-agents docs |
| Skills can declare hooks that register on invocation and persist for the rest of the process | Confirmed, skills docs and a local experiment. They do not survive `--resume`, also from that experiment |
| `${CLAUDE_SKILL_DIR}` is not substituted in frontmatter hook commands, and Bash and hooks get `CLAUDE_CODE_SESSION_ID` | Confirmed, local experiment on 2.1.322 and the env-vars docs |
| `UserPromptSubmit` also fires for background subagent reports, scheduled tasks and cross-session messages | Confirmed, hooks docs |
| `UserPromptSubmit` input carries the submitted `prompt` and `session_id` | Confirmed, hooks docs |
| `PostToolUse` fires only on success, and Bash's `tool_response` has `stdout` and `stderr` but no exit code | Confirmed, hooks docs |
| `transcript_path` points at a JSONL file under `~/.claude/projects/`, written asynchronously | Confirmed, hooks docs and local files |
| The transcript's record schema stays parseable for the fallback | Assumed, undocumented, so the fallback fails closed |
| Managed settings may disable skill hooks, leaving only the fallback | Assumed from the skills docs note on `strictPluginOnlyCustomization` |
| Prompt suggestions can pre-fill answers and `promptSuggestionEnabled: false` turns them off | Confirmed, interactive-mode and settings docs. SKILL.md tells the learner once |
| Obsidian graph view counts frontmatter links | Assumed. Body links make it moot |
| The person, not the repo, owns the store | Assumed. Changes paths and the evidence-protocol "ledger in the repo" rule if wrong |
| The thresholds (2 passes over 2 days, `hint_max` 2, the ladder, 15 lines) are reasonable | Assumed, all configurable, no direct evidence for the exact values |
| A multi-turn simulator can drive evals through one `claude -p --input-format stream-json` process | Confirmed for the hook by a local experiment. The draft's `-p` plus resume would have lost the witness |
| LearnHarness ideas can be reused under AGPL without copying wording | Confirmed license. Own wording only is a hard rule for the builder |
| The name `learn-ledger` is free | Confirmed 2026-11-13, skills.sh and GitHub code search |

## Build checklist

1. Name checked on skills.sh and GitHub, done 2026-11-13.
2. Write the script tests and forged logs, then the model eval fixtures, learner profiles and simulator driver. Run the baseline arm first (RED).
3. `ll.py` store, locked append, schema validation, and the seal, pose, answer, reveal, grade guards.
4. `levels` and `due` exactly as specified, until the script tests pass.
5. The witness hook, `answer --from-witness`, confidence parsing, and the `verify` fallback.
6. `status`, written for a reader who has just lost all context.
7. Propositions, chains, `similar`, `distill-input`, `snippet` and `ledger`.
8. `export` and its layout test.
9. `hook post-commit`, `session-start`, `optin`, `offer`, and `install --print`.
10. `agents/examiner.md` and `agents/distiller.md`.
11. `references/pedagogy.md` and `references/ledger.md`, in our own wording.
12. SKILL.md last, under 3,500 tokens measured, with the non-negotiables and the `status`-first rule in the first 1,500.
13. Run with-skill evals (GREEN), close loopholes (REFACTOR), then trigger evals.
14. Register the `L` prefix, the store, and the fixtures in evidence-protocol.md, add the README entry, and extend the pipeline line to say learn-ledger tests the human on what the others explain.
15. One adversarial-verify round on SKILL.md and scripts, fixing only wrong-action bugs.

## Scope and non-goals

Not an app, MCP server, or hosted service.
Not a security gate or proof of authorship, and it never blocks git.
No trace capture or simulated runtime behavior, which belongs to microworld.
No reviewer-facing brief, which belongs to explain-changes.
No mastery claim beyond "answered correctly, witnessed, on these days".
No flashcard UI. Obsidian is a generated view, never the source of truth.
Claude Code only for the witness. Elsewhere answers stay `pending` and earn no level.

## Open risks

1. **Grading is still model judgment.** The seal fixes the key, not the leniency. The `check-queue` and `teach-closures` evals compare grades with the simulator's known truth, and a cross-model grader is future work.
2. **Open book with an agent at hand.** A witnessed answer may have been asked of another agent. Disclosed in `status`, and not solvable by a skill.
3. **Time cost.** Engagement techniques cost about 1.8 to 2.7 times the time in Kazemitabaar et al., so learners may opt out, and the no-nag limits also lower the dose.
4. **Hook availability.** Managed settings or non-Claude-Code hosts remove the witness, and then nothing earns levels.
5. **Taught content can be wrong.** Model-asserted propositions are marked `unverifiable`, and their correctness rests on adversarial-verify being run.
6. **The thresholds and ladder are judgment calls.** They are configurable, and only real use will tune them.
7. **Simulated learners are not people.** The evals prove the protocol runs, not that anyone learned more.
