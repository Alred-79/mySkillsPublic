# The ledger

What `ll.py` stores and computes, for a human reader and for anyone changing the script.
The full design and its reasoning are in [docs/specs/learn-ledger.md](../../docs/specs/learn-ledger.md).

## Store

`~/.learn-ledger/`, or `LEARN_LEDGER_HOME`, because learning belongs to the person across repos.

| File | Content |
|---|---|
| `config.json` | `vault_path`, `ladder`, `review_size`, `hint_max_qualify`, offer limits, `ignore_globs`, `similar_threshold` |
| `events.jsonl` | the append-only source of truth, appended under an exclusive lock |
| `sealed/<qid>.json` | each committed question, hashed in its `seal` event |
| `witness.jsonl` | prompts captured by the hook while a question was open in that session |
| `propositions.jsonl`, `chains.jsonl` | append-only, merged on read, the first line for an id defines it and provenance unions |

Every event has `v`, `id` (sequential, so time-ordered), `ts`, `day` (local date), `session` (from `CLAUDE_CODE_SESSION_ID`), `mode`, `type`.

| `type` | Fields |
|---|---|
| `node` | `node`, `topic`, `title`, `parents` |
| `teach` | `node`, `text`, `props` |
| `seal` | `qid`, `node`, `kind`, `topic`, `sha256`, `prompt_hash`, `repo`, `rev`, `backup_of` |
| `pose` | `qid` |
| `answer` | `qid`, `text`, `confidence`, `dont_know`, `witness` (`hook` or `pending`), `witness_id`, one per hint rung |
| `verify` | `qid`, `answer`, `witness` (`witnessed` or `unwitnessed`), settling a pending answer from the transcript |
| `reveal` | `qid`, `hash_ok` |
| `grade` | `qid`, `verdict`, `miss_class`, `wrong_model`, `hint_max` |
| `dispute` | `qid`, `reason` |
| `offer`, `accept`, `decline`, `pause`, `reminder` | `repo`, `rev` or `until` |
| `distilled` | `teach_ids`, `props`, `chains` |

## The gate

`seal`, then `pose`, then `answer`, then `reveal`, then optional hint-rung `answer` calls, then `grade`.
`pose` refuses a qid with no seal.
A second `answer` before `reveal` is refused.
`reveal` refuses before an answer, rechecks the sealed file's hash, and exits 3 on a mismatch.
`grade` refuses unless the order is seal, pose, answer, reveal and every reveal's hash matched, and refuses `pass` on a don't-know.

## Witness

The skill's frontmatter declares a `UserPromptSubmit` hook running `ll.py hook witness`.
It records a prompt only while a question is posed and ungraded in that session, and never a slash command.
`answer --from-witness` takes the prompt witnessed since the pose (or since the previous answer), refuses when there is none, and asks for `--witness ID` when there are several.
Skill hooks last for one Claude Code process, so after `--resume` the skill must be invoked again before it witnesses anything.
`answer --text` is logged `pending`, and `verify` later looks for the text as a user message in `~/.claude/projects/*/<session>.jsonl` after the pose.
Found is `witnessed`, absent is `unwitnessed`, and a pending answer in the current session younger than ten minutes stays pending, since the transcript is written asynchronously.

## Levels

Per node, from graded attempts in valid order and not disputed, each judged on its last answer.

1. An attempt qualifies for kind k when it passed, its answer was witnessed (`hook` or `witnessed`), it was not don't-know, `hint_max` was at most 2, and for K1 it was cold.
2. Cold means no `teach` on that node and no `reveal` of another question on that node earlier in the same session.
3. Kind k is met when, among the attempts after its most recent non-passing attempt (fail, partial or don't-know, witnessed or not), at least two qualify on different `prompt_hash` values and different days.
4. The level is the largest L for which K1 through KL are all met.

Levels appear only in `levels`, `status` and the vault's `_progress.md`.

## Review schedule

Each (node, kind) with at least one scheduling pass is an item, where a scheduling pass is a pass that is witnessed, not don't-know, and at rung R2 or below.

1. Walk its attempts in order with `n = 0` and no anchor. `interval(n) = ladder[min(n, 5)]`, default `[1, 3, 7, 16, 35, 75]` days.
2. Anything other than a scheduling pass sets `n = 0` and the anchor to its day.
3. A scheduling pass with no anchor yet, or at least `ceil(interval(n) / 2)` days after the anchor, adds one to `n` and moves the anchor. An earlier one changes nothing.
4. `due_day = anchor + interval(n)`, due when today is on or after it.
5. Weakest first sorts by last attempt a miss, lower `n`, lower kind, more chains using the node as a premise, older last attempt.
6. Up to `review_size` items, interleaved so no two in a row share a node whenever some order allows it. If one node dominates, not-yet-due items from other nodes are padded in, nearest due first. If the store has a single node, `due` says so.

## Offers

`hook post-commit` stays silent unless the Bash command was a `git commit` in the main conversation (no `agent_id`) whose output shows a created commit, the commit changed at least `min_changed_lines` outside `ignore_globs`, no offer was made this session, fewer than `max_offers_per_day` today, no `seal` already names this repo and commit, no decline this session, the last two responses were not both declines within `decline_backoff_hours`, and offers are not paused or off.
`hook session-start` shows a `systemMessage` once a day at startup when at least `reminder_min_due` items are due.
Both hooks live in settings, which only the user edits, from `hook install --print`.

## Commands

```
ll.py init [--vault PATH]
ll.py status
ll.py node add --topic T --id N --title S [--parents A,B]
ll.py teach --node N --file STEP.md [--props P1,P2]
ll.py seal --node N --kind K [--mode teach|review|check] [--repo R --rev SHA] < packet.json
ll.py pose QID
ll.py answer QID (--from-witness [--witness W] | --text S)
ll.py reveal QID
ll.py grade QID --verdict pass|partial|fail [--miss-class C] [--wrong-model W] [--hint-max 0-5]
ll.py dispute QID --reason S
ll.py levels [--topic T]
ll.py due [--size N] [--json]
ll.py verify
ll.py prop add "STATEMENT" [--topic T] [--id ID] [--source S] [--provenance E1,E2] [--force --reason R]
ll.py prop similar "STATEMENT" [--threshold X]
ll.py chain add --premises P1,P2 --conclusion P3 [--provenance E1]
ll.py distill-input [--topic T] [--done E1,E2 --props P1 --chains C1]
ll.py snippet FILE:START-END [--rev R]
ll.py ledger [--topic T] [--repo PATH]
ll.py export [--vault PATH]
ll.py optin (--pause 7d | --off | --on)
ll.py offer (accept | decline) [--rev SHA]
ll.py hook (witness | post-commit | session-start | install --print)
```

Refusals exit 2 with the reason on stderr, and a hash mismatch at reveal exits 3.
`LL_NOW` overrides the clock for tests and evals only.

## `L` assertion rows

`ledger` prints propositions and the keys of revealed check-mode questions in the evidence-protocol table.
A `file:line@rev` source that `snippet` can read is `verified`, a URL is `proposed` until someone checks it, `model-asserted` is `unverifiable`, and a disputed question is `disputed`.
An unrevealed key, such as an unused backup scenario, never appears.

## Obsidian export

`export` writes only under `<vault>/learn-ledger/`, regenerates it wholesale, and refuses to touch that folder if it holds anything it did not generate.

```
<vault>/learn-ledger/
  README.md                    generated-view notice, source is the store
  _progress.md                 level map and due queue, the only levels in the vault
  topics/<topic>.md            links to the topic's propositions
  propositions/<id>-<slug>.md  statement, source, provenance, "Premise of [[<cid>]]"
  chains/<cid>.md              premises as plain text, "These jointly imply [[<id>-<slug>]]"
```

Graph view drops direction, so direction lives in who links whom.
A premise links to its chain and the chain links only to its conclusion, so the backlinks pane shows the reverse.
Every wikilink names a full file basename, so every link resolves.
