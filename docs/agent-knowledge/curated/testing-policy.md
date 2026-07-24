# Curated testing policy

## Required test characteristics

- Use `unittest` and keep tests deterministic.
- Prefer small fakes for `PaymentGateway` and `PaymentRepository` boundaries.
- Do not mock `Order` or `Payment` value objects.
- Assert both the returned value and relevant dependency interactions.
- Test names must describe observable behavior.
- Do not modify production code merely to make a generated test pass unless the task explicitly requests a production fix.

## Required agent workflow

1. Read `.agent-runtime/active-context.md` when present.
2. Read the relevant generated module page and curated rules.
3. Query the target symbol with the `test-knowledge` skill.
4. Inspect the current implementation.
5. Add the smallest useful test change.
6. Run `make test` and `make check`.
7. Report the exact knowledge files and graph query used.
