-- 0007_add_orders.sql
-- Hand-written migration. Representative of the SQL the team ships by hand;
-- it is the kind of input a SQL-review skill would analyze statically.

CREATE TABLE orders (
    id            bigserial PRIMARY KEY,
    customer_id   bigint NOT NULL,
    status        text NOT NULL DEFAULT 'pending',
    total_cents   bigint NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Non-concurrent index build on what will become a large, hot table: takes an
-- ACCESS EXCLUSIVE-adjacent lock and blocks writes for the duration. The kind
-- of migration-safety issue H1/N2 want caught.
CREATE INDEX idx_orders_customer ON orders (customer_id);

-- Backfill on the same transaction as the DDL above.
UPDATE orders SET status = 'migrated' WHERE status = 'pending';
