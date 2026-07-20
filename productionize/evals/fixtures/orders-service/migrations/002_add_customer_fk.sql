-- Migration 002: link orders to customers and require a region.
-- Runs against the live production database during deploy.

-- VIOLATION (B4): this migration sets NO lock_timeout and NO statement_timeout. Each of
-- the statements below takes ACCESS EXCLUSIVE on a hot, actively-queried table. If the
-- DDL queues behind even one slow read, every query behind it blocks for the read's full
-- remaining duration and the API goes down for that window. The fixes: SET lock_timeout
-- to a low value (e.g. 2s) so the DDL gives up instead of holding the queue, add the FK
-- as NOT VALID then VALIDATE separately, and add the NOT NULL column in the
-- expand-contract style (nullable + backfill + constraint) rather than in one shot.

-- adds and validates a foreign key in a single blocking step (should be NOT VALID first)
ALTER TABLE orders
  ADD CONSTRAINT orders_customer_fk FOREIGN KEY (customer_id) REFERENCES customers (id);

-- adds a NOT NULL column with a default in one shot on a hot table
ALTER TABLE orders
  ADD COLUMN region text NOT NULL DEFAULT 'us-east';

-- NOTE (B10): the settlement job below does read-modify-write on order balances assuming
-- REPEATABLE READ prevents lost updates. On MySQL it does not (Jepsen); even on Postgres a
-- concurrent update needs SELECT ... FOR UPDATE or a version column. The assumption is
-- documented here so the audit can check the engine's real guarantee against it.
