# Prompts for the demo

## Agents tab: generate the deliberately missing idempotency test

```text
Use the test-generator agent.
Add a test for repeated idempotency keys in PaymentService.authorize.
Before editing, report knowledge freshness, find PAYMENT_GRAPH_PROBE_7F31,
and query PaymentService.authorize at depth 1.
Modify tests only, then run the required checks.
```

Expected behavior: the second call returns the original `Payment`, does not call the gateway again, and does not persist again.

## Agents tab: evaluate the existing suite

```text
Use the test-evaluator agent to evaluate PaymentService.authorize.
Do not edit files. Compare current tests with the static branch inventory and curated domain rules.
```

## Knowledge maintenance

```text
Use the knowledge-curator agent after changing production code.
Regenerate the graph and knowledge pack, review the diff, and run all checks.
```

## VS Code / Copilot CLI

```text
Use the test-knowledge skill. Prepare context, query PaymentService.authorize,
and explain which knowledge files are authoritative for the current branch.
```
