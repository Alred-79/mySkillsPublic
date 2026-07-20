// Retry helpers used across the service.

// VIOLATION (B1): fixed-delay retry with NO jitter and NO cap on total time.
// This is layered on top of other retries (see paymentClient below and the mesh
// config in k8s/virtualservice.yaml, which ALSO retries), so the same call path is
// retried at multiple layers: (1 + 3)^2 = 16 attempts for one user action, with every
// client backing off in lockstep (no jitter => synchronized retry storms).
async function retry(fn, attempts = 3, delayMs = 200) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, delayMs)); // fixed delay, no jitter
    }
  }
  throw lastErr;
}

// DO NOT CUT (reliability-critical retry, correctly built): this one has full jitter,
// a bounded number of attempts, AND a hard deadline budget. It guards the single
// idempotent read of the exchange-rate service, which is flaky but safe to retry.
// Cutting or "simplifying" this retry removes a legitimate resilience mechanism.
// It is the control: a correct retry that must survive the audit untouched.
async function retryWithJitter(fn, { attempts = 4, baseMs = 100, deadlineMs = 2000 } = {}) {
  const start = Date.now();
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    if (Date.now() - start > deadlineMs) break; // retry budget: stop before the deadline
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const backoff = baseMs * 2 ** i;
      const sleep = Math.random() * backoff; // full jitter
      await new Promise((r) => setTimeout(r, sleep));
    }
  }
  throw lastErr;
}

module.exports = { retry, retryWithJitter };
