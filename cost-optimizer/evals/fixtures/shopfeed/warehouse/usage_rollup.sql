-- Daily usage rollup for the analytics dashboard. Runs every morning against BigQuery.
-- `events` is partitioned by DATE(event_ts) and clustered by merchant_id.

-- VIOLATION (C8): SELECT * with NO partition filter on a partitioned+clustered table. BigQuery
-- on-demand bills per BYTES SCANNED ($6.25/TiB, tebibyte, first 1 TiB/mo free, captured 2026-07).
-- Selecting every column and every partition scans the whole table each day even though the query
-- needs three columns and one day. A partition predicate on DATE(event_ts) plus selecting only the
-- needed columns cuts scanned bytes by ~80-95%, cutting the bill proportionally.
-- Fix below the violation.
SELECT *
FROM `shopfeed.analytics.events`
WHERE merchant_id IN (SELECT merchant_id FROM `shopfeed.analytics.active_merchants`);

-- What it should look like (needed columns + partition filter):
-- SELECT event_ts, merchant_id, amount
-- FROM `shopfeed.analytics.events`
-- WHERE DATE(event_ts) = CURRENT_DATE() - 1
--   AND merchant_id IN (SELECT merchant_id FROM `shopfeed.analytics.active_merchants`);

-- DECOY (clean): this query is already well-scoped - explicit columns, partition filter. Do NOT
-- flag it as a full-scan.
-- SELECT merchant_id, SUM(amount) AS revenue
-- FROM `shopfeed.analytics.events`
-- WHERE DATE(event_ts) BETWEEN CURRENT_DATE() - 7 AND CURRENT_DATE()
-- GROUP BY merchant_id;
