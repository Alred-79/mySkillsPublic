# orders-service

Order intake and fulfillment API. Takes orders over HTTP, persists them, charges the customer, and fans out post-order side effects (confirmation email, downstream webhooks).

This is the service that takes money, so it is business-critical: an outage or a double charge is a real incident.

## Stack

- Runtime: Node.js + Express (`src/server.js`)
- Datastore: PostgreSQL (`src/db.js`, `migrations/`), `max_connections = 100`
- Queue/bus: RabbitMQ for `order.created` events (`src/orders.js`); an in-process queue for emails (`src/queue.js`)
- Orchestrator: Kubernetes + Istio (`k8s/`), 8 replicas
- Downstreams: payments service, FX rate service, email service (all internal)
- Config: hot-reloaded from a config service (`src/config.js`)

## Run

```
npm install
npm run migrate
npm start
```

## Endpoints

- `POST /orders` - create an order, charge the customer, queue the confirmation email
- `GET /healthz` - liveness
- `GET /readyz` - readiness

We are launching a marketing push next week and expect roughly 5x normal traffic. We want to know whether this service will hold up.
