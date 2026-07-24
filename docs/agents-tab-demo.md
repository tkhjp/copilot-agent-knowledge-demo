# GitHub Agents tab demo

This walkthrough demonstrates how repository files, custom agents, an Agent Skill,
and a session-start freshness hook work together. Agent sessions provide provenance;
the committed knowledge pack provides reusable handoff context.

## Prerequisites

- GitHub Copilot cloud agent is enabled for the account and repository.
- This repository's files are merged into its default branch.
- GitHub Actions is enabled.
- The custom agent profiles under `.github/agents/` are visible in the agent picker.

The special setup workflow `.github/workflows/copilot-setup-steps.yml` prepares Python
before a cloud-agent session starts. The repository hook then prepares the active
knowledge context inside the agent sandbox.

## Demo 1: generate the intentionally missing idempotency test

The starter suite intentionally omits the existing-payment branch. In the repository's
**Agents** tab:

1. Start a new agent task.
2. Select the repository and its default branch.
3. Select the `test-generator` custom agent.
4. Submit this prompt:

   ```text
   Add the missing unit test for PaymentService.authorize when an idempotency key
   already has a saved payment.

   Before editing:
   - use the test-knowledge skill;
   - report the active knowledge mode;
   - find PAYMENT_GRAPH_PROBE_7F31;
   - query PaymentService.authorize at depth 1.

   Modify tests only. Prove that the original Payment object is returned, the gateway
   is not called, and the repository does not save again. Run make test and make check,
   then open a pull request with knowledge provenance in the summary.
   ```

5. Open the session log and confirm that the session-start hook ran
   `python3 -m tools.knowledge.prepare_context --hook`.
6. Review the resulting pull request. Its summary should identify:
   - active knowledge mode;
   - current source digest;
   - generated and curated files read;
   - graph query used;
   - validation commands and results.

## Demo 2: prove branch-aware freshness

Create a branch that changes `PaymentService.authorize` without running
`make knowledge`. Start a `test-generator` session against that branch and use:

```text
Analyze the changed PaymentService.authorize behavior and propose the minimum tests
needed. Do not edit files. State whether committed or runtime knowledge is active,
show the committed and current source digests, and list the runtime knowledge files.
```

Expected behavior:

```text
committed source digest != current source digest
    -> .agent-runtime/ is generated from the current branch
    -> the agent uses runtime knowledge before the committed baseline
```

The current source remains authoritative even when runtime generation succeeds.

## Demo 3: refresh the shared baseline

After an accepted source change, select the `knowledge-curator` agent and submit:

```text
Regenerate and validate the deterministic code graph and Agent Knowledge Pack for
this branch. Do not alter production behavior or curated policy. Explain every
knowledge artifact that changes, run make check, and open a pull request.
```

Alternatively, run the manual **Refresh Agent Knowledge** workflow. It creates a pull
request only when deterministic generated output changes.

## Demo 4: evaluate generated tests

Select `test-evaluator` and submit:

```text
Evaluate the tests in the current branch for PaymentService.authorize. Do not edit
files. Check knowledge freshness, query the target at depth 1, run make test and
make check, and report behavioral gaps, weak assertions, nondeterminism, and exact
knowledge provenance.
```

## What the team shares

Copilot cloud-agent sessions appear in **Agents -> All sessions** and are visible to
repository collaborators. Use the session to review prompts, commands, responses,
and file changes. Do not use the session as the authoritative knowledge database.

The reusable handoff is:

```text
source commit or branch
+ artifacts/codegraph/
+ docs/agent-knowledge/
+ pull request and validation results
```
