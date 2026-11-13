# Expected: ground truth per case

Scoring follows evidence-protocol.md, with a skill arm and a no-skill baseline arm on the same prompts and the same simulated learner, at least 3 reps on at least 2 model tiers.
HARD FAIL rows are pass^k, they must hold on every rep.
Mechanical rows are scored by `scripts/score.py` from the store and the stream, and judged rows by `judge/rubric.md`.
These evals measure protocol fidelity against simulated learners, not human learning.

## Status

The script tests run and pass, `python3 evals/scripts/test_ll.py`, 59 tests, deterministic, no model.
The driver was smoke-run on single reps to prove the plumbing, which is not a benchmark.

| Run | Result |
|---|---|
| `one-off`, haiku, both arms | both answered plainly, no events in the skill arm's store |
| `teach-closures`, skill arm, haiku and sonnet, first attempt | invalid. The driver's tool allowlist lacked `Skill`, so the skill call was denied, and score.py's H0 row now fails such a run instead of passing it vacuously |
| `teach-closures`, skill arm, sonnet, after the fix | H0 to H5 pass. 8 questions sealed and posed, 7 answers credited, all matching what the simulator sent, the seeded mutable-default misconception surfaced as a graded miss, "just tell me" graded at R5, "skip" logged as don't-know |

The benchmark itself, every case at 3 reps on 2 tiers in both arms, has not been run, so no uplift number is claimed yet.

## Script tests (must be 100%)

| Rule | Fixture or setup |
|---|---|
| Two passes on one day do not meet a kind, two days do | `logs/same-day`, `logs/two-days` |
| A pass at rung R3 does not qualify | `logs/hint3` |
| An unwitnessed pass does not qualify | `logs/unwitnessed` |
| A warm K1 pass does not qualify | `logs/warm-k1` |
| A fail resets its kind, witnessed or not | `logs/fail-reset`, `logs/unwitnessed-fail` |
| A disputed attempt is dropped | `logs/disputed` |
| The level stops at the first unmet kind | `logs/gap-at-k3`, `logs/level-4` |
| `grade` refuses a seal logged after its answer, and before reveal | forged log, live cycle |
| `reveal` detects an edited sealed file and grading is then refused | live cycle |
| Hint-rung retries log several answers and grade the last | live cycle |
| The witness records nothing without an open question, nothing from another session, never a slash command, and requires a choice between two prompts | live hook calls |
| `--text` answers stay pending until the transcript settles them | synthetic transcript |
| `due` reproduces the hand-computed queue, the single-node note, the reset after a heavily hinted pass, no credit for cramming, and padded greedy interleaving | `review-due/store`, `review-due/store-single-node`, built logs |
| Every post-commit limit fires, including the subagent and failed-commit cases | real git repo per test |
| The reminder is a once-a-day `systemMessage`, never model context | `review-due/store` |
| `export` writes the documented layout, every wikilink resolves, chains link only their conclusion, no level appears in a proposition note, and a folder it did not generate is left alone | `review-due/store` |
| `ledger` never shows an unrevealed key, `status` never shows the open question's key | live cycle |
| The frontmatter hook command finds `ll.py` without `${CLAUDE_SKILL_DIR}` and exits 0 when it cannot | fake home |
| Security, ids are validated and export never writes outside its folder, front matter values cannot add keys, `snippet` refuses absolute, escaping, symlinked and store paths, and the transcript fallback needs a whole-message match that is not part of the question | forged store lines, live calls |
| `score.py` passes a clean run, catches each HARD FAIL, and fails a skill arm that never ran the protocol | synthetic runs |

## teach-closures

Learner profile `learners/closures.json` holds functions and a one-line idea of closures, believes a mutable default is fresh on every call (answers "f(1) is [1] and f(2) is [2]" at 85), says "just tell me" at question 3 and "skip" at question 5.

- The probe reaches the mutable-default strand and surfaces the misconception, and a sealed packet names it as a wrong model.
- Any claim about what `f(1); f(2)` prints comes from running it (`[1]` then `[1, 2]`).
- "just tell me" yields the answer and is logged as rung 5, and "skip" is logged as don't-know, not a fail typed by the tutor.
- The close retests the miss on a fresh surface (a different mutable default, such as a dict or a set), distills propositions, and prints `ll.py levels`.
- No level claim beyond the printed map. After one session every kind has at most one day of passes, so every level is 0, and a tutor that says the learner "has got it" or reached a level fails H3.

Baseline proxy. A no-skill tutor is expected to ask several questions per message, give the answer on the first miss, never commit a reference answer before the learner replies, praise in mastery terms, and persist nothing.
The judge scores whether a reference answer was stated or implied before the learner replied, which a baseline cannot show.

## check-queue

The change adds `worker.py`, which commits the charge before acking the job.
A crash between `ledger.commit()` and `queue.ack()` leaves the job unacked, so it is redelivered after the visibility timeout and charged twice. `python3 worker.py` prints `acct-9 charged 2500 cents` for one 1250-cent job.
The chat history claims "we chose ack-after-commit for latency" and "exactly once", which is the agent's narration and is wrong on the second count.

- H4. The canary sentence never appears in any Agent or Task tool prompt.
- At least one question targets duplicate charge on redelivery, with a key that says charged twice and cites `worker.py`.
- The learner misses that question once (profile), gets the reveal, then the sealed backup scenario (a `seal` with `backup_of`), not a rewording.
- Code shown is verbatim (H5).

Baseline proxy. Without the skill, the same model answers from its own context and tends to restate "exactly once" from the chat, and asks about names or quizzes from memory of what it wrote.

## review-due

Store `review-due/store`, clock fixed at 2026-03-10.

| Node | Kind | History | n | Due | State |
|---|---|---|---|---|---|
| left-join | K2 | pass 03-01, fail 03-09 | 0 | 03-10 | due, last a miss |
| semi-join | K2 | pass 03-03 | 1 | 03-06 | due |
| cross-join | K3 | pass 02-20, pass 02-24 | 2 | 03-03 | due |
| inner-join | K2 | pass 03-01, pass 03-04 | 2 | 03-11 | not due |
| anti-join | K3 | pass 03-02, pass 03-05 | 2 | 03-12 | not due |

`ll.py due` returns left-join K2, semi-join K2, cross-join K3, in that order.
The tutor seals a fresh question per item of that kind from the node's propositions (`p0001` to `p0005`), and the learner's WHERE-filter misconception surfaces on left-join.

## review-single-node

Store `review-due/store-single-node`. Only left-join K2 is due, and `due` prints the single-node note. The tutor runs it without pretending to interleave and varies the surface.

## one-off

"what's a mutex?" gets a plain answer, no sealed question, no loop.

## nag

The project's settings carry the hooks from `ll.py hook install --print`.
The first commit (about 30 changed lines in `worker.py`) qualifies, so one offer appears after the task is done, and the learner says "no thanks".
The second qualifying commit in the same session gets no offer, and the README commit is docs-only and gets none either.
The store holds exactly one `offer` and one `decline`.
The baseline has no hook and never offers, so this case guards the skill against nagging rather than measuring uplift.

## Thresholds

Script tests 100%.
HARD FAIL rows hold on every rep.
With-skill mean on scored rows at least 0.85, and uplift over the baseline at least 0.30.
Rows passing 100% in both arms are pruned while the seed is kept.

## Trigger evals

`trigger-evals.json`, about 20 queries, each run 3 times with a 60/40 split.
Pass at least 0.8 on should-trigger and at most 0.2 false triggers.
Not run yet.
