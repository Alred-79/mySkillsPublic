# Prior agent's research answer: "Which HTTP status code for rate limiting, and what does the spec say about Retry-After?"

Handed off for verification. Claims R1-R4.

- **R1.** The correct status code for a rate-limited request is **429 Too Many Requests**,
  defined in RFC 6585. (factual - clean control: this is correct)

- **R2.** The `Retry-After` header may be sent with a 429 response to tell the client how
  long to wait, and its value may be either an integer number of seconds or an HTTP-date.
  (factual - clean control: this is correct, per RFC 9110)

- **R3.** As of mid-2026, the HTTP semantics specification in force is **RFC 7231**, which
  is the current authority for the `Retry-After` header definition. (factual - PLANTED
  STALE FACT: RFC 7231 was obsoleted by RFC 9110 in June 2022; 9110 is the current
  authority)

- **R4.** The 429 status code is in the 4xx client-error class, so a well-behaved client
  should not retry the exact same request without first waiting. (factual - clean control:
  correct)

Note for the verifier: there is exactly one stale/obsoleted-spec claim here. The others are
current. Do not flag the correct ones.
