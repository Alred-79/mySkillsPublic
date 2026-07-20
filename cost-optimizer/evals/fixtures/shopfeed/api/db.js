// Postgres access for the order path.

const { Pool } = require("pg");
const pool = new Pool({ max: 10 });

// VIOLATION (C9): N+1 / query-in-a-loop. One SELECT per item id, in a loop, instead of a single
// batched `WHERE id = ANY($1)`. At order scale this multiplies round trips and DB compute (and,
// on a consumption-priced DB, billed read units) by the item count. This is the exact pattern
// the empirical evidence says LLMs have near-zero recall on ("Bigger Isn't Always Better", arXiv;
// verify id before quoting) - a true delta.
// Fix: one query with an IN / ANY list; add an index on the filtered column if missing.
async function getOrderItems(itemIds) {
  const out = [];
  for (const id of itemIds) {
    const { rows } = await pool.query("SELECT id, price FROM items WHERE id = $1", [id]);
    out.push(rows[0]);
  }
  return out;
}

async function getFxRate(currency) {
  const { rows } = await pool.query("SELECT rate FROM fx WHERE currency = $1", [currency]);
  if (!rows[0]) throw new Error("no rate");
  return rows[0].rate;
}

async function chargeCard(card, amount) {
  // calls the external payment provider; each call is billed per request by the provider
  return callPaymentProvider(card, amount);
}

// MUST-NOT-CUT (reliability-critical decoy): the settlement audit log. This is verbose, but it
// is the SOLE audit trail for money movement (regulatory + dispute evidence), not debug noise.
// Cutting it to reduce log volume loses the audit trail - a hard fail. Contrast with the
// ORDER_DEBUG line in handler.js (C10), which is genuine hot-path debug spam and SHOULD be cut.
async function recordSettlement(orderId, amount, providerRef) {
  const { rows } = await pool.query(
    "INSERT INTO settlement_audit (order_id, amount, provider_ref, at) VALUES ($1,$2,$3, now()) RETURNING id",
    [orderId, amount, providerRef],
  );
  console.log("SETTLEMENT_AUDIT", JSON.stringify({ orderId, amount, providerRef, auditId: rows[0].id }));
  return rows[0].id;
}

function callPaymentProvider(card, amount) {
  return Promise.resolve({ id: "ch_stub" });
}

module.exports = { getOrderItems, chargeCard, getFxRate, recordSettlement };
