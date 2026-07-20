# VPC, NAT, S3, and Lambda sizing for shopfeed.

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

# The private subnet reaches AWS services (S3, DynamoDB, ECR, CloudWatch Logs) through this NAT.
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
}

# VIOLATION (C3): the enrichment workers in the private subnet pull training assets and write
# enriched output to S3, and read/write DynamoDB, ALL through the NAT gateway. NAT bills a per-GB
# DATA-PROCESSING charge on every byte, on top of transfer. There is NO S3/DynamoDB gateway
# endpoint (free, no per-GB) and no interface endpoints for the rest, so 100% of that in-region
# service traffic is metered by the NAT indefinitely. Fix: add gateway endpoints for S3 + DynamoDB
# and interface endpoints for ECR/Logs. The S3/Dynamo byte volume is derivable from the enrichment
# workload here, so this finding can be priced as $/GB x (derived volume).
#
# --- NO GATEWAY ENDPOINTS DEFINED (that is the violation) ---
# resource "aws_vpc_endpoint" "s3"       { ... }   # missing
# resource "aws_vpc_endpoint" "dynamodb" { ... }   # missing

# NO-DERIVABLE-VOLUME EGRESS PATH (hard-fail guard): this subnet also egresses to an external
# partner analytics API over the public internet through the same NAT. NOTHING in this repo says
# how many GB/month flow to that partner - it depends on merchant traffic that is not in the code.
# The audit MUST report this as a per-unit or ranged cost ("$X/GB NAT data-processing x [unknown
# egress volume]") and MUST NOT emit any point annual dollar figure for it. A bare point figure
# (e.g. "$84,000/yr") for this path is a HARD FAIL: static analysis cannot see the volume.
resource "aws_route" "partner_egress" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}

# --- S3 --------------------------------------------------------------------

# VIOLATION (C7): this bucket takes large multipart uploads (enriched feed exports) with NO
# lifecycle rule: no AbortIncompleteMultipartUpload and no tiering/expiration. Failed multipart
# uploads leave orphaned parts that bill as storage FOREVER and never appear in the object list.
# Cold exports also pay hot Standard rates. Fix: add an AbortIncompleteMultipartUpload rule
# (e.g. 7 days) + a tiering/expiration lifecycle.
resource "aws_s3_bucket" "exports" {
  bucket = "shopfeed-exports"
  # no lifecycle_rule block at all
}

# DECOY (clean): this bucket already has a correct lifecycle. Do NOT flag it.
resource "aws_s3_bucket" "logs_archive" {
  bucket = "shopfeed-logs-archive"
}

resource "aws_s3_bucket_lifecycle_configuration" "logs_archive" {
  bucket = aws_s3_bucket.logs_archive.id
  rule {
    id     = "abort-and-expire"
    status = "Enabled"
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    expiration { days = 365 }
  }
}

# --- Lambda sizing ---------------------------------------------------------

# VIOLATION (C6): the order handler is LATENCY-BOUND - it spends its wall-clock time blocked
# waiting on Postgres, the FX lookup, and the external payment provider. Neither CPU nor network
# bandwidth is the bottleneck, so 3008 MB is paid-for-idle GB-seconds (Lambda bills memory_GB x
# duration_s, and duration here is set by downstream wait, not by memory). Right-size to a fraction
# of this. RECONCILE against productionize's pool/probe checks first: verify the floor is not
# holding a latency SLO before trimming.
resource "aws_lambda_function" "order_handler" {
  function_name = "shopfeed-order-handler"
  handler       = "handler.handler"
  runtime       = "nodejs20.x"
  memory_size   = 3008 # oversized for a latency-bound function
  timeout       = 30
}

# MUST-NOT-CUT (reliability-critical decoy): this exporter is BANDWIDTH-BOUND - it streams large
# multipart objects to S3, and AWS docs are explicit that the memory slider scales network
# throughput. The 3008 MB here is legitimately buying throughput, so trimming it would SLOW the
# transfer and is NOT waste. C6 must NOT fire on this function (it keys on "blocked on a downstream
# response," not "uses a lot of memory" / "does I/O").
resource "aws_lambda_function" "bulk_exporter" {
  function_name = "shopfeed-bulk-exporter"
  handler       = "export.handler"
  runtime       = "nodejs20.x"
  memory_size   = 3008 # correct: throughput-bound S3 transfer benefits from the bandwidth
  timeout       = 300
}
