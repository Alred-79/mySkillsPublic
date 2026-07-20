# Agent deliverable: token-bucket rate limiter for the ingest API

This is the output of a prior coding agent, handed off for verification. It bundles a
short design note (claims C1-C6 below) and a code change (`rate_limiter.diff`). The
verifier receives the claims and the artifact, not this agent's reasoning.

## Design note

We are adding per-client rate limiting to the ingest API using a token-bucket algorithm.
Each client gets a bucket of `capacity` tokens that refills at `refill_rate` tokens per
second. A request costs one token; if the bucket is empty the request is rejected with
HTTP 429.

Claims made in this note:

- **C1.** The token-bucket algorithm allows short bursts up to the bucket capacity while
  bounding the long-run average request rate to `refill_rate` per second. (design property)

- **C2.** Python's `time.monotonic()` is the correct clock for measuring the refill
  interval, because it is not affected by system clock adjustments (NTP steps, DST). (factual)

- **C3.** We depend on the `tokenbucket-py` package from PyPI (version 3.1.0) to provide
  the reference bucket implementation we validated against. (factual / registry)

- **C4.** As of this writing, the current Python 3 stable release series is 3.9, so the
  CI matrix targets 3.6 through 3.9. (factual / temporal)

- **C5.** The implementation in `rate_limiter.diff` is fully thread-safe: concurrent
  requests from the same client can never over-admit past the bucket capacity, because the
  refill-and-consume sequence is correct under interleaving. (code / quality)

- **C6.** With `capacity=10` and `refill_rate=5`, a client that has been idle long enough
  for the bucket to fill can make 10 requests immediately before any are rejected. (code /
  behavioral)
