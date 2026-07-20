// Order intake Lambda. Validates the order, charges the customer, fans out post-order work.

const { getOrderItems, chargeCard, getFxRate } = require("./db");

// --- retry helpers -------------------------------------------------------

// VIOLATION (C2): fixed-delay retry, no jitter, no attempt budget, no cap that sheds load.
// Used below to retry the charge call. At a downstream failure rate f, uncapped synchronized
// retries multiply offered load toward 1/(1-f) (~2x at f=0.5), and every metered thing on the
// path (compute-seconds, the per-call payment-provider charge) is billed on the amplified count.
// Shares the retry detector with productionize; here the finding is PRICED, not just hardened.
async function retry(fn) {
  for (;;) {
    try {
      return await fn();
    } catch (e) {
      await sleep(1000); // fixed 1s, no jitter, loops forever
    }
  }
}

// MUST-NOT-CUT (reliability-critical decoy): this retry is CORRECT - full jitter, a hard
// attempt cap, and a total time budget, guarding a flaky-but-idempotent GET (the FX rate).
// It is the only backstop for a rate lookup that blips. Removing or weakening it to "save"
// anything is a hard fail: the skill audits retries, it does not delete legitimate resilience.
async function retryWithJitter(fn, { maxAttempts = 4, budgetMs = 8000 } = {}) {
  const start = Date.now();
  let attempt = 0;
  for (;;) {
    try {
      return await fn();
    } catch (e) {
      attempt += 1;
      if (attempt >= maxAttempts || Date.now() - start > budgetMs) throw e;
      const base = Math.min(1000 * 2 ** attempt, 4000);
      await sleep(Math.random() * base); // full jitter
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// --- handler -------------------------------------------------------------

exports.handler = async (event) => {
  const order = JSON.parse(event.body);

  // DECOY (clean): input validation is present and correct. "Add validation" is a false positive.
  if (!order || !Array.isArray(order.items) || order.items.length === 0) {
    return { statusCode: 400, body: "invalid order" };
  }

  const items = await getOrderItems(order.items); // see db.js (C9)
  const fx = await retryWithJitter(() => getFxRate(order.currency)); // correct retry - keep it
  const total = items.reduce((s, it) => s + it.price * fx, 0);

  // VIOLATION (C10): full per-request debug logging on the hot path. Every order logs the entire
  // item list plus computed fields. Log INGESTION is billed per GB; at order volume this line's
  // ingestion cost can exceed the Lambda compute cost. Should sample/aggregate, and drop full-body
  // logging on the hot path (keep error-path logs). NOTE: this is plain debug noise, NOT an audit
  // trail - contrast with the settlement audit log in db.js, which must be kept.
  console.log("ORDER_DEBUG", JSON.stringify({ order, items, fx, total }));

  const charge = await retry(() => chargeCard(order.card, total)); // jitterless retry (C2)

  return { statusCode: 200, body: JSON.stringify({ orderId: charge.id }) };
};
