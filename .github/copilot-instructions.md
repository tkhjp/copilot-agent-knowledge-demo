# Repository-wide Copilot instructions

This repository demonstrates an Agent Knowledge Loop for test generation.

Before generating, changing, or reviewing tests:

1. Use the `test-knowledge` skill.
2. Read `.agent-runtime/active-context.md` when present.
3. Read the relevant files under `docs/agent-knowledge/generated` or the runtime path named by the active context.
4. Read `docs/agent-knowledge/curated/domain-rules.md` and `docs/agent-knowledge/curated/testing-policy.md`.
5. Query the exact target symbol with graph depth 1.
6. Verify all knowledge against current source code.

Knowledge precedence is:

1. current working-tree source;
2. runtime branch knowledge under `.agent-runtime`;
3. committed generated knowledge;
4. curated rules;
5. Wiki pages, issues, pull requests, memories, and Agent session history.

Run `make test` and `make check` after code or test changes. Never hand-edit generated knowledge or raw graph artifacts.
