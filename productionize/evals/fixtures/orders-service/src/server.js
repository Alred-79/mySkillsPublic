const express = require('express');
const { liveness, readiness } = require('./health');
const { createOrder, initBus } = require('./orders');
const { charge } = require('./payment');
const { enqueue, worker } = require('./queue');
const { retryWithJitter } = require('./retry');
const { reload, get: getConfig } = require('./config');
const axios = require('axios');

const app = express();
app.use(express.json());

// hot-reload runtime config on SIGHUP (config service pushes then signals). Unguarded:
// a bad config push throws in reload() and crashes the process (B5).
process.on('SIGHUP', reload);

app.get('/healthz', liveness);
app.get('/readyz', readiness);

// DO NOT CUT: the exchange-rate lookup uses the correct jittered, budgeted retry. This is
// a legitimate resilience mechanism guarding a flaky-but-idempotent GET. It must survive.
async function getRate(currency) {
  return retryWithJitter(async () => {
    const res = await axios.get(`${process.env.FX_URL || 'http://fx.internal'}/rate/${currency}`);
    return res.data.rate;
  });
}

app.post('/orders', async (req, res) => {
  // DECOY (clean): input validation is present and correct; do not report "add validation".
  const { customerId, amountCents, currency } = req.body || {};
  if (!customerId || !Number.isInteger(amountCents) || amountCents <= 0) {
    return res.status(400).json({ error: 'invalid order' });
  }

  const cfg = getConfig();
  if (cfg.ordersPaused) {
    return res.status(503).json({ error: 'orders paused' });
  }

  const rate = await getRate(currency || 'USD');
  const id = await createOrder({ customerId, amountCents });
  await charge(id, Math.round(amountCents * rate)); // retried POST, no idempotency key (B7)

  enqueue(async () => {
    await axios.post(`${process.env.EMAIL_URL || 'http://email.internal'}/send`, { orderId: id });
  });

  res.status(201).json({ id });
});

// DECOY (clean): a correct 404 handler. Not a finding.
app.use((req, res) => res.status(404).json({ error: 'not found' }));

const server = app.listen(process.env.PORT || 3000, async () => {
  await initBus();
  worker();
});

// VIOLATION (B6): exit-now SIGTERM handler. On every deploy Kubernetes sends SIGTERM and
// this process exits immediately, while the load balancer is still routing to it for the
// endpoint-propagation window. Result: 502s on every single rollout. The handler must
// fail readiness first, wait for propagation, drain in-flight requests, THEN exit.
process.on('SIGTERM', () => {
  process.exit(0);
});

module.exports = { app, server };
