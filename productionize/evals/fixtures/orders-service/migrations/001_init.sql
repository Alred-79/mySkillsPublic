-- Initial schema.
-- Postgres is provisioned with max_connections = 100 (see infra; do not raise it blindly).

-- VIOLATION (B4, secondary): orders.id is a 32-bit serial (int4). On a high-volume orders
-- table this exhausts at ~2.1B rows and the INSERT starts failing hard. High-volume PKs
-- should be bigserial/identity from the start.
CREATE TABLE orders (
  id          serial PRIMARY KEY,
  customer_id integer NOT NULL,
  amount_cents integer NOT NULL,
  status      text NOT NULL DEFAULT 'created',
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customers (
  id   integer PRIMARY KEY,
  name text NOT NULL
);
