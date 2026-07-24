---
name: test-knowledge
description: Prepare fresh branch-aware repository knowledge and query narrow code-graph slices before generating, changing, or evaluating tests.
---

Use this skill for any task that generates, changes, reviews, or evaluates tests.

## Procedure

1. Ensure branch-aware context exists:

   ```bash
   .github/skills/test-knowledge/prepare-context
   ```

2. Read `.agent-runtime/active-context.md`.
3. Read the relevant generated module page under the path named in the active context.
4. Read `docs/agent-knowledge/curated/domain-rules.md` and `docs/agent-knowledge/curated/testing-policy.md`.
5. Query only the target symbol and a small neighborhood:

   ```bash
   .github/skills/test-knowledge/query-graph --symbol PaymentService.authorize --depth 1
   ```

6. Verify every behavioral claim against the current source code.
7. Treat static relationships and branch inventories as candidate evidence, not proof of runtime coverage.
8. Run the relevant tests and `make check` after edits.
9. In the final response, list:
   - current Git HEAD;
   - committed knowledge freshness status;
   - generated knowledge paths used;
   - the graph query used;
   - tests and checks executed.

Never use a shared Agent session, Wiki page, issue, or pull request comment as the authoritative description of current code. Those surfaces provide provenance and human collaboration, while repository files and current source provide executable context.
