# Curated domain rules

These rules are intentionally maintained by humans. Generated code-graph output must not overwrite this file.

## Payment authorization

- `PAYMENT_GRAPH_PROBE_7F31` is the retrieval probe for this demo.
- A repeated idempotency key returns the original `Payment` object.
- When an existing payment is returned, the gateway must not be called and the repository must not save again.
- Non-positive amounts are rejected before gateway or repository write operations.
- The gateway is retried exactly once after `TimeoutError`.
- A second timeout is translated to `PaymentGatewayUnavailable`.
- Repository persistence happens only after successful authorization.

## Authority

Current source code is authoritative. When these rules conflict with the implementation, stop and report the inconsistency rather than silently generating a test against an obsolete rule.
