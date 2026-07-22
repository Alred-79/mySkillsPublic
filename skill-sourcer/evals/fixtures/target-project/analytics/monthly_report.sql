-- monthly_report.sql
-- Hand-written analytics query. Representative input for static SQL review.

-- Join fan-out risk: one order with several items inflates SUM(o.total_cents).
-- A correctness bug a review skill (H1) should flag.
SELECT
    c.id                         AS customer_id,
    c.name                       AS customer_name,
    SUM(o.total_cents)           AS revenue_cents,
    COUNT(*)                     AS line_items
FROM customers c
JOIN orders o        ON o.customer_id = c.id
JOIN order_items oi  ON oi.order_id = o.id
WHERE o.created_at >= date_trunc('month', now())
GROUP BY c.id, c.name
ORDER BY revenue_cents DESC;
