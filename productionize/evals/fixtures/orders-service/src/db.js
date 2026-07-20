const { Pool } = require('pg');

// VIOLATION (B9): pool of 200 per instance. We run 8 instances (see k8s/deployment.yaml,
// replicas: 8), so 1600 connections against a Postgres max_connections of 100 (see
// migrations/001_init.sql comment). Oversized pools collapse latency; smaller is faster.
// There is also no connectionTimeoutMillis, so a request waits forever for a connection
// under saturation (an outage in disguise).
const pool = new Pool({
  host: process.env.PGHOST || 'localhost',
  port: process.env.PGPORT || 5432,
  user: process.env.PGUSER || 'orders',
  password: process.env.PGPASSWORD || 'orders',
  database: process.env.PGDATABASE || 'orders',
  max: 200,
  idleTimeoutMillis: 30000,
});

module.exports = { pool };
