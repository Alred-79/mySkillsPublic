# Spec: Shared Evidence Protocol

Status: approved design, pre-implementation
Applies to: all skills in this repo (adversarial-verify, fix-issue, revamp-ui, statistician,
microworld, productionize, cost-optimizer, better-tools, skill-sourcer, explain-changes)

Assertion `id` prefixes registered: `A` claims (adversarial-verify), `H` hypotheses
(fix-issue), `D` dials/contract terms (revamp-ui, statistician tier), `M` microworld
capture/check rows, `P` productionize findings/fixes/demonstrations, `C` cost-optimizer
findings/estimates, `T` better-tools recommendations, `S` skill-sourcer recommendations,
`E` explain-changes brief claims.

## Why this exists

Every competing skill ships in isolation. This repo's signature is a **suite with shared
infrastructure**: claims (adversarial-verify), hypotheses (fix-issue), and contract dials
(revamp-ui) are all the same underlying thing - *assertions with an evidence status*. One
ledger format lets the skills compose natively:

- adversarial-verify can audit a fix-issue evidence ledger directly.
- revamp-ui's DESIGN-CONTRACT doubles as a verification packet.
- Any future skill in the repo inherits verification for free by emitting assertions.

## The assertion record

Ledgers are markdown files with a table (human-readable, greppable, no tooling required).
Each assertion row:

| Field | Values | Notes |
|---|---|---|
| `id` | A1, H2, D3... | prefix by kind: A=claim, H=hypothesis, D=dial/contract term |
| `assertion` | free text | one checkable statement |
| `status` | `proposed` / `verified` / `refuted` / `disputed` / `unverifiable` | disputed = credible evidence contradicts; unverifiable = no evidence found (these are different findings) |
| `evidence` | citation | file:line, command + output summary, URL + access date |
| `expiry` | date or `stable` | freshness-sensitive assertions get a re-check-after date |
| `risk` | high / medium / low | blast radius if wrong; drives verification effort ordering |

Rules all skills follow:

1. **Evidence is required for any terminal status.** No status change without a citation.
2. **`unverifiable` is a finding, never a pass.**
3. **Prediction before observation** (fix-issue): a hypothesis row records its predicted
   observation *before* the experiment runs; the evidence field records predicted vs actual.
4. **Ledgers persist in the repo being worked on** (e.g. `.evidence/` or a task-local file),
   surviving context compaction and sessions.

## Cross-session memory files

| File | Written by | Read by | Content |
|---|---|---|---|
| `bugs-learned.md` (repo-level) | fix-issue autopsy phase | fix-issue triage (grepped first: "seen this class before?") | root cause, bug class, discriminating evidence, why it was missed |
| taste profile (user-level, `~/.claude/.../taste-profile.md` or repo `.design/`) |  revamp-ui interview + every bolder/quieter correction | revamp-ui interview (pre-fills defaults) | dial history, aesthetic families chosen, corrections made |
| verifier calibration log | adversarial-verify | adversarial-verify (tunes skepticism) | claims that passed verification but later proved wrong |
| dataset gotchas (repo-level, `data-gotchas.md`) | statistician Phase 1/4 | statistician Phase 0 (grepped at start) | per-dataset traps confirmed once (grain, timezone, key duplication, definition quirks) |
| microworld ledger rows (prefix `M`, working repo's ledger) | microworld capture/check | adversarial-verify (audits artifact claims; `cannot_claim` seeds the unverified surface) | isolation receipt, freshness hashes (expiry = on source/dep/runtime change), check gate results |

Skill-local artifacts (NOT assertion ledgers, by design): statistician's implicit-test
counter and forking-paths deviation log are counts/logs, not assertions - they live
beside the ledger, and the chosen rigor tier is recorded as a `D` assertion row.

## Eval fixtures (shipped proof)

Each skill folder ships a colocated `evals/` directory (`evals.json`, `fixtures/`,
`expected.md`, `judge/` where applicable - layout in the Eval rules section below) so downloaders
can prove the skill works (and so we honor writing-skills TDD - these fixtures ARE the
pressure tests from the RED phase, kept):

- fix-issue: a mini-project with a planted multi-component bug (plus a planted red herring).
- revamp-ui: a slop-ridden page exhibiting the named banned defaults.
- adversarial-verify: a document + diff with seeded errors (stale fact, subtle logic bug,
  overclaim) that a rubber-stamping verifier would bless.
- statistician: seeded-trap datasets (fan-out join, day/month dates, non-normal small-n,
  Simpson's stratification, implicit multi-test bait, leakage bait, baseline bait).
- microworld: small Python fixture repos with a seeded surprising behavior (plus a
  nondeterministic decoy that must fail capture).
- productionize: a small service seeded with operational blindspot violations (layered
  retries without jitter, DB-pinging liveness probe, lockless migration, dual write,
  exit-now SIGTERM, unbounded queue, stale flag) plus clean decoys.
- cost-optimizer: a polyglot app seeded with tier-1/2/3 cost violations (unbounded agent
  loop, jitterless retry, NAT-egress IaC, caching-off static prompt, Opus-on-trivial-calls,
  over-provisioned Lambda, no S3 lifecycle, `SELECT *` on a partitioned table, N+1) plus
  clean decoys, a reliability-critical retry the skill must NOT cut, and a no-derivable-
  volume egress path (emitting any point annual dollar figure for it is a hard fail).
- better-tools: a polyglot repo with real opportunities (hand-rolled parse a library does
  better, a deprecated dep with a live successor, two overlapping deps, a heavy dev-tool
  with a lighter swap) plus poisoned bait - a guaranteed-permanently-invalid package name,
  an EOL/abandoned package, a trendy-but-immature package, and a stdlib-suffices case.
- skill-sourcer: a project + prompt with explicit requirements, and a seeded skill pool
  - a relevant+safe+maintained skill (ranks first), a popular-but-off-target skill (must
  not rank high), an abandoned skill, a hallucinated/nonexistent repo, a typosquatted owner,
  and four malicious skills (literal `curl | bash`, packed/obfuscated, prose prompt-injection,
  and a sandbox-aware skill that behaves in a trial - the trial must never clear it).
- explain-changes: a small repo plus a seeded change delivered as a patch, with an
  intent-parrot trap (the commit subject claims a behavior the diff does not add), a
  cross-file blast-radius split (one call site the change reaches, one it does not), a
  must-flag unverifiable (a rounding mode whose downstream agreement is not derivable),
  a happy-path-only test so "verified" must come from a real run, and a scope decoy plus
  a one-line-change fixture guarding over-production.

No public skills repo ships eval fixtures; this is both a credibility signal and the
regression suite for future skill edits.

## Eval rules (shared across all skills)

Repo rule: **no skill ships without an eval.** Each skill's spec defines its own eval
architecture; the eval artifacts live in that skill's `evals/` folder:

```
<skill>/evals/
  evals.json     # eval cases (skill-creator schema: id, prompt, files, expectations)
  fixtures/      # seeded inputs, clean controls, before-states
  expected.md    # per-case ground truth / required gates
  judge/         # judge prompts + rubrics, where an LLM judge is used
```

Rules every skill's eval follows (stated once here so they cannot drift):

1. **Evals before extensive skill text** - write the cases and run the no-skill
   baseline first (this is the RED phase of writing-skills TDD, formalized).
2. **Uplift, not absolute score**: every benchmark runs with-skill vs baseline, paired
   runs in parallel in clean contexts. Keep the baseline forever - when the no-skill
   arm starts passing, that's the skill's obsolescence signal.
3. **≥3 replicates per condition, mean ± stddev.** Single runs lie. Variance is itself
   a metric: converging reps with the skill vs scattered without = guidance is binding.
4. **Checklist, not golden answer** for anything subjective; score objectively only
   what MUST be true, judge the rest.
5. **Trigger evals are separate**: ~20 realistic queries (8–10 should-trigger, 8–10
   near-miss should-NOT-trigger), each run 3×, 60/40 train/test split so the
   description isn't overfit.
6. **Frontier tasks only** - drop ceiling-effect tasks; prune assertions that pass
   100% in both arms (they measure nothing).
7. **Test on ≥2 model tiers** - uplift is inversely correlated with model capability.
8. **Judge-bias mitigations wherever an LLM judge is used**: swap A/B order and count
   only consistent verdicts; instruct on verbosity; anonymize provenance; allow
   "Unknown" verdicts; isolated judge per dimension; periodic human calibration.
9. **Tooling**: reuse the installed skill-creator harness (paired runs,
   `aggregate_benchmark.py`, blind comparator/analyzer agents, eval-viewer,
   `run_loop.py` for trigger-description optimization) - emit its schemas; the shared
   harness is repo-level, keeping skill payloads lean.
