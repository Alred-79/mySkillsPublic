# pricing (microworld eval fixture)

A tiny two-file Python shop-pricing module. No third-party dependencies; pure
Python, single process, deterministic where it matters.

- `checkout.py` - the **seeded surprising behavior** and the intended microworld
  target. `price_order` composes a percentage discount and a flat coupon and
  decides free shipping. Two priors a reviewer would reasonably hold are wrong:
  discount steps do **not** commute (the percentage step truncates to whole
  cents before the coupon applies), and free shipping is judged on the
  **pre-discount** subtotal, not the amount actually paid. Same input -> same
  output on every run, so it is a valid world to capture and replay.

- `fraud.py` - the **nondeterministic decoy that must fail capture**.
  `risk_score` mixes the amount with `time.time()` and `random.random()`, so two
  captures of the same input differ. An honest adapter must reject it at the
  double-capture determinism gate rather than fabricate a stable trace. The
  values are injectable, so the correct fix (declare the clock/random as inputs
  or mocked-boundary seams) is available - but as called with defaults, it fails,
  and that rejection is the point.

The microworld should build its world around `checkout.price_order` and, if it
touches `fraud.py` at all, demonstrate that path failing the determinism gate -
never present a made-up fraud score as captured.
