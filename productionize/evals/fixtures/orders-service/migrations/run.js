const fs = require('fs');
const path = require('path');
const { pool } = require('../src/db');

// Applies every .sql file in this directory in name order. No lock_timeout or
// statement_timeout is set around the DDL (see B4 in the migration files themselves).
async function run() {
  const files = fs
    .readdirSync(__dirname)
    .filter((f) => f.endsWith('.sql'))
    .sort();
  for (const f of files) {
    const sql = fs.readFileSync(path.join(__dirname, f), 'utf8');
    console.log(`applying ${f}`);
    await pool.query(sql);
  }
  await pool.end();
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
