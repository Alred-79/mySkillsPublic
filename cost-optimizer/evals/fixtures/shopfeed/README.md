# shopfeed

Product-feed enrichment and order service. Ingests a merchant's raw product feed, enriches each
item with an LLM (category, summary, tags), takes orders over HTTP, charges the customer, and rolls
usage up into a warehouse for analytics.

The bill has been climbing and nobody is sure why. We spend on AWS (compute, storage, data transfer),
on an LLM provider (the enrichment + a support agent), on a data warehouse, and on our observability
stack. We want to know where the money is going and what to cut.

## Stack

- Enrichment + support agent: Python, Anthropic SDK (`agent/`)
- API: Node.js Lambda behind API Gateway (`api/`), Postgres for orders
- Infra: Terraform (`infra/`) - VPC with private subnets, a NAT gateway, S3 buckets
- Warehouse: BigQuery, queried from dbt/SQL (`warehouse/`)
- Observability: logs shipped to a per-GB-ingestion vendor

## Run

```
cd agent && pip install -r requirements.txt && python enrich.py
cd api && npm install && npm start
terraform -chdir=infra apply
```

## Layout

- `agent/enrich.py` - per-item LLM enrichment (runs over the whole feed)
- `agent/support_agent.py` - a tool-using support agent
- `agent/requirements.txt`
- `api/handler.js` - order intake, charge, fan-out
- `api/db.js` - Postgres access
- `infra/main.tf` - VPC, NAT, S3, Lambda sizing
- `warehouse/usage_rollup.sql` - the daily analytics query
