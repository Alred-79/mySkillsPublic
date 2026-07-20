"""Fraud scoring for an order - the NONDETERMINISTIC DECOY.

This module exists to be a trap. `risk_score` mixes the order amount with the
wall clock and a fresh random draw, so two captures of the same input produce
DIFFERENT scores. Any honest microworld adapter that tries to build a world
around this MUST fail the double-capture determinism gate: run it twice, the
canonical traces differ, capture is rejected.

The correct move is exactly what the protocol prescribes: this code path depends
on real nondeterminism (a clock and randomness), so it cannot be replayed
faithfully. To bring it into a world you would have to inject `now` and the
random value as declared inputs, or declare them as mocked-boundary seams. As
written, it fails capture, and that failure is the right outcome - not something
to paper over by averaging or picking one run.
"""
import random
import time


def risk_score(amount_cents, now=None, jitter=None):
    """A 0-99 'risk' score.

    `now` and `jitter` default to live, uncontrolled sources. When they are left
    as defaults the function is nondeterministic; that is the seeded trap. (They
    are injectable so the lesson is complete: passing fixed values makes it
    deterministic, which is how you would actually declare the seam.)
    """
    if now is None:
        now = time.time()          # wall clock: changes every call
    if jitter is None:
        jitter = random.random()   # fresh randomness: changes every call

    base = (amount_cents // 100) % 50
    wobble = int((now * 1000) % 25)
    noise = int(jitter * 25)
    return (base + wobble + noise) % 100
