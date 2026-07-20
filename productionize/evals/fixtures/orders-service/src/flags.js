// Feature flags. Read from env at boot.

// DECOY (clean): a live, owned, dated flag. Owner and expiry present. This is how a
// flag should look; it must NOT be reported as debt.
// owner: payments-team  expiry: 2026-09-01  purpose: gate the new settlement path
const NEW_SETTLEMENT_ENABLED = process.env.NEW_SETTLEMENT_ENABLED === 'true';

// VIOLATION (B12): stale + repurposed flag. It was created in 2021 to gate a "fast
// checkout" experiment that shipped long ago. The name was later quietly reused to skip
// inventory reservation during an incident, so flipping it now runs a DIFFERENT, dormant
// code path than the name implies. No owner, no expiry. Dead code reachable via config.
const FAST_CHECKOUT = process.env.FAST_CHECKOUT === 'true';

function skipInventoryReservation() {
  // repurposed meaning: this used to mean "fast checkout", now gates reservation-skip
  return FAST_CHECKOUT;
}

module.exports = { NEW_SETTLEMENT_ENABLED, FAST_CHECKOUT, skipInventoryReservation };
