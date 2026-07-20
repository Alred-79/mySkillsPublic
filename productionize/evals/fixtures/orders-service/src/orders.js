const { pool } = require('./db');
const amqp = require('amqplib');

let channel;
async function initBus() {
  const conn = await amqp.connect(process.env.AMQP_URL || 'amqp://localhost');
  channel = await conn.createChannel();
  await channel.assertExchange('orders', 'topic', { durable: true });
}

// VIOLATION (B8): dual write. The row is committed to Postgres, then a SEPARATE publish
// goes to RabbitMQ. There is no transactional outbox and no CDC between them. If the
// process dies after COMMIT but before publish (or the broker is briefly down), the
// order exists in the DB but no downstream ever hears about it: guaranteed divergence
// over enough orders. The two writes are not atomic and nothing reconciles them.
async function createOrder(order) {
  const { rows } = await pool.query(
    'INSERT INTO orders (customer_id, amount_cents, status) VALUES ($1, $2, $3) RETURNING id',
    [order.customerId, order.amountCents, 'created']
  );
  const id = rows[0].id;

  // second write to a different system, no atomicity with the COMMIT above
  channel.publish('orders', 'order.created', Buffer.from(JSON.stringify({ id, ...order })));

  return id;
}

module.exports = { initBus, createOrder };
