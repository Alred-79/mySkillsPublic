const fs = require('fs');

// Runtime config is fetched from a config service and hot-reloaded, on a DIFFERENT path
// than code deploys: it lands instantly, globally, with no canary and no staging.

// VIOLATION (B5): the config blob is JSON.parse'd with no schema validation, no size cap,
// and the parse is unguarded, so a malformed push throws and crashes the process on the
// hot path. There is no last-known-good fallback: one bad config edit takes the whole
// fleet down at once, the CrowdStrike / Cloudflare config-as-code-deploy shape.
function loadConfig() {
  const raw = fs.readFileSync(process.env.CONFIG_PATH || '/etc/orders/config.json', 'utf8');
  return JSON.parse(raw); // throws on bad input, no validation, no fallback
}

// applied on every hot reload
let current = loadConfig();
function reload() {
  current = loadConfig();
}

module.exports = { loadConfig, reload, get: () => current };
