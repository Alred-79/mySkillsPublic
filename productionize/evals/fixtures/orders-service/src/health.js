const { pool } = require('./db');

// VIOLATION (B3): liveness probe pings the database. If Postgres has a brief blip, every
// pod fails liveness at once and Kubernetes restarts the whole fleet, turning a short DB
// hiccup into a restart storm that guarantees an outage. Liveness must depend on NOTHING
// external; it should answer "is this process wedged?", not "is my database up?".
async function liveness(req, res) {
  try {
    await pool.query('SELECT 1');
    res.status(200).send('ok');
  } catch (e) {
    res.status(500).send('db down');
  }
}

// DECOY (clean): readiness legitimately checks a dependency (that is what readiness is
// for), and failing readiness only deregisters this one pod from the load balancer
// rather than restarting it. This is correct and must NOT be flagged as the liveness bug.
async function readiness(req, res) {
  try {
    await pool.query('SELECT 1');
    res.status(200).send('ready');
  } catch (e) {
    res.status(503).send('not ready');
  }
}

module.exports = { liveness, readiness };
