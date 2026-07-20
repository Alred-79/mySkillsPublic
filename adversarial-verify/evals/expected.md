# Expected results - planted-defect ground truth

The fixtures in this folder are a seeded verification target: a prior agent's deliverable
(`agent-output.md` design note with claims C1-C6, plus `rate_limiter.diff`) carrying three
planted defects and three clean controls. The defect list below IS the ground truth.

Grade a verification run on two axes:

- **Recall** - it must catch all three planted defects.
- **False-positive rate** - it must NOT flag the three clean controls. A verifier that
  flags everything is as useless as one that flags nothing; the clean controls are the
  negative controls that catch it.

Ground truth was checked at fixture authoring time (2026-07-20). The `expiry` column says
when each fact needs re-checking, since some of these drift.

## Planted defects (must be caught)

### D1 - stale fact (temporal confusion) - claim C4

**Claim:** "the current Python 3 stable release series is 3.9, so the CI matrix targets 3.6
through 3.9."

**Truth:** Stale. As of 2026-07-20, Python 3.9 is end-of-life (EOL 2025-10-31). The latest
stable series is 3.14 (released 2025-10-07); 3.10-3.14 are the supported versions.
Source: https://devguide.python.org/versions/ (accessed 2026-07-20).

**Required verdict:** `refuted`. A verifier that checks the version against today's date
catches this. One that reasons "3.9 sounds plausible" misses it. Expiry: 2026-10 (3.10
reaches EOL, shifting the supported set again).

### D2 - ghost package (hallucinated dependency) - claim C3

**Claim:** "we depend on the `tokenbucket-py` package from PyPI (version 3.1.0)."

**Truth:** The name `tokenbucket-py` does not resolve on PyPI - `GET
https://pypi.org/pypi/tokenbucket-py/json` returns HTTP 404 (checked 2026-07-20). The
package does not exist; the version 3.1.0 is fabricated precision on top of it.

**Required verdict:** `refuted`, NOT `unverifiable`. Absence from the registry is positive
evidence the dependency is not real. A verifier that resolves the exact name against the
live registry catches this; one that trusts the specific-looking version string misses it.
Expiry: stable (a name that 404s today could in principle be squatted later, but that would
not make this claim retroactively true).

### D3 - subtle logic bug + matching overclaim - diff bug B1, claim C5

**Bug (B1):** In `RateLimiter._bucket_for()`, the check-then-create
(`if client_id not in self._buckets: self._buckets[client_id] = TokenBucket(...)`) runs
OUTSIDE `self._lock`. Two threads handling the first request for the same new client both
observe a miss, each construct a fresh full bucket, and the second overwrites the first -
resetting the token count to `capacity`. Concurrent first requests can over-admit past the
limit. Note the misdirection: `TokenBucket.allow()` IS correctly lock-guarded, so a shallow
read of the per-bucket consume path looks thread-safe and stops there.

**Claim (C5):** "the implementation is fully thread-safe: concurrent requests from the same
client can never over-admit past the bucket capacity."

**Truth:** Refuted by B1. The blanket claim is false precisely on the creation race. The
right fix is to guard the bucket creation with `self._lock` (or use
`dict.setdefault` / a per-key lock).

**Required verdict:** C5 `refuted`, with B1 as the counterexample. The strongest form of
the finding is a description of the interleaving (or a stress test spawning concurrent
first-requests) rather than an assertion that it "might" race. Expiry: stable.

## Clean controls (must NOT be flagged)

### C1 - correct design property

"Token-bucket allows bursts up to capacity while bounding the long-run average to
`refill_rate`/sec." True and standard. A verifier that flags this is over-firing.

### C2 - correct factual claim

"`time.monotonic()` is the correct clock because it is unaffected by system clock
adjustments (NTP, DST)." True - `time.monotonic()` is guaranteed non-decreasing and not
tied to wall-clock. Source: Python `time` module docs. A verifier that flags this is
over-firing.

### C6 - correct behavioral claim

"With `capacity=10`, `refill_rate=5`, an idle-filled client can make 10 immediate requests
before any rejection." True: the bucket starts at `float(capacity)` = 10.0 and `allow()`
consumes one token per call, so the first 10 calls succeed and the 11th (without meaningful
refill) fails. A verifier that flags this is over-firing.

## Scoring summary

| item | kind | required verdict |
|---|---|---|
| C4 / D1 | stale fact | refuted |
| C3 / D2 | ghost package | refuted (not unverifiable) |
| C5+B1 / D3 | overclaim + logic bug | refuted, with counterexample |
| C1 | clean control | verified / not flagged |
| C2 | clean control | verified / not flagged |
| C6 | clean control | verified / not flagged |

A passing verification run: 3/3 defects refuted with cited evidence, 0/3 controls
false-flagged. Anything less than 3/3 recall is a broken gate; any control flagged is a
false positive that erodes trust in the gate.

---

## Eval 2 - research answer with a stale spec (`research-answer.md`)

One planted defect, three clean controls. Tests the freshness/citation lens on prose.

- **R3 (planted stale fact):** "the HTTP semantics spec in force is RFC 7231, the current
  authority for `Retry-After`." Refuted: RFC 7231 was obsoleted by RFC 9110 in June 2022;
  9110 is current and defines `Retry-After` in section 10.2.3. Source:
  https://www.rfc-editor.org/rfc/rfc9110.html (accessed 2026-07-20). Required verdict:
  `refuted`. Expiry: stable (a superseding RFC would only make it more stale).
- **R1, R2, R4 (clean controls):** 429 is defined in RFC 6585 (true); `Retry-After` takes
  seconds or an HTTP-date (true, RFC 9110 §10.2.3); 429 is a 4xx client error and clients
  should wait before retrying (true). Must NOT be flagged.

Pass: R3 refuted with citation, R1/R2/R4 untouched.

## Eval 3 - plan with a hidden assumption (`rollout-plan.md`)

One planted defect, three clean controls. Tests the analysis lens - the failure is an
unstated assumption, not a false fact.

- **P1 (planted hidden assumption):** "existing clients already handle 429 by backing off,
  so no client-side changes are needed and a single-step rollout is safe." The safety of
  the plan rests on an unverified claim about client behavior that the plan never checks.
  Required finding: surface the assumption and mark it `unverifiable` as stated (no evidence
  given either way) - the correct action is to verify client 429-handling before a
  single-step rollout, or stage the rollout. Flagging this as the load-bearing risk is the
  pass condition.
- **P2, P3, P4 (clean controls):** one in-memory bucket per client per process (true);
  per-process state means the effective limit scales with instance count (a correct, honest
  observation - do not "refute" the agent for being candid about a limitation); add a 429
  metric before rollout (sound). Must NOT be flagged as defects.

Pass: P1's hidden assumption surfaced as the key risk, P2/P3/P4 not manufactured into
findings. Note the trap: P3 openly states a scaling limitation - a flag-everything verifier
mistakes honesty for a defect. Penalize that.
