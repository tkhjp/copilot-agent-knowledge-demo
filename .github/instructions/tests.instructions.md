---
applyTo: "tests/**/*.py,**/test_*.py"
---

- Use Python `unittest`.
- Prefer fakes at protocol boundaries over mocks of value objects.
- Assert observable results and relevant interactions.
- Query the production symbol before adding a test.
- Current source is authoritative when generated knowledge is stale or contradictory.
- Run `make test` and `make check` after changes.
