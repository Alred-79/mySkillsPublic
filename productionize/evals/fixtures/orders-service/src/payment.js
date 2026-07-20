const axios = require('axios');
const { retry } = require('./retry');

const PAYMENTS_URL = process.env.PAYMENTS_URL || 'http://payments.internal:8080';

// VIOLATION (B7 + B1): this POST charges a card. It is wrapped in retry() (jitterless,
// see retry.js) and the mesh retries it again, yet the request carries NO idempotency
// key. A retried charge is a double charge. Money path with no dedupe is the textbook
// idempotency failure: the effect (the charge) is not tied to a key persisted with it.
async function charge(orderId, amountCents) {
  return retry(async () => {
    const res = await axios.post(`${PAYMENTS_URL}/charges`, {
      order_id: orderId,
      amount_cents: amountCents,
      // no idempotency_key
    });
    return res.data;
  });
}

module.exports = { charge };
