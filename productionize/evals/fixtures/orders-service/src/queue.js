// In-process work queue for post-order side effects (emails, webhooks).

// VIOLATION (B2): unbounded in-memory queue. Under load, or when the worker stalls on a
// slow downstream, this array grows without limit until the process OOMs. There is no
// max depth, no backpressure, and no shedding of work whose deadline has already passed.
// This is a sustaining feedback loop: a slow downstream makes the queue grow, which makes
// memory pressure worse, which slows everything, which grows the queue further.
const pending = [];

function enqueue(job) {
  pending.push(job); // no bound, no drop-oldest, no reject-when-full
}

async function worker() {
  for (;;) {
    const job = pending.shift();
    if (job) {
      try {
        await job();
      } catch (e) {
        // swallow and continue
      }
    } else {
      await new Promise((r) => setTimeout(r, 50));
    }
  }
}

module.exports = { enqueue, worker, pending };
