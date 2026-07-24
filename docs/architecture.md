# Architecture notes

## Design objective

Enable multiple GitHub Copilot agents and developers to share code-derived knowledge that stays fresh enough for test-generation tasks without depending on Copilot Spaces, MCP, or another agent's session history.

## Separation of responsibilities

| Layer | Responsibility |
|---|---|
| Source | current executable truth |
| Raw graph | precise machine relationships |
| Generated knowledge | compact retrieval surface for agents |
| Curated knowledge | human policy and domain semantics |
| Skill | repeatable method for selecting and querying knowledge |
| Hook | deterministic freshness preparation |
| Custom Agent | role-specific behavior and validation |
| Session | provenance and collaborative review |
| Wiki | human-facing navigation and publication |

## Why sessions are not the knowledge database

Sessions are valuable for understanding rationale and reviewing an agent's actions. They are not a stable, repository-wide query index for later agents. The durable handoff must therefore be a commit, branch, pull request, or other versioned artifact.

## Why the graph has a projection

Large raw graphs create retrieval noise and consume context. The projection exposes a compact index and lets an agent request a symbol-level slice only when needed.

## Freshness invariant

A knowledge pack is current when its recorded input digest equals the digest of current source inputs and its schema/generator versions match the installed tooling.

This invariant works with committed files, uncommitted working trees, feature branches, and cloud-agent sandboxes without requiring a self-referential commit hash.

## Agent-first execution path

```text
Agent task starts
    -> copilot-setup-steps prepares the language environment
    -> sessionStart hook compares committed and current source digests
    -> fresh: use committed graph and Markdown projection
    -> stale: generate .agent-runtime graph and projection from current source
    -> Agent Skill selects a narrow symbol-level graph slice
    -> custom agent edits or evaluates tests
    -> tests, checks, pull request, and shared session record the outcome
```

## Knowledge authority

The demo applies this precedence order consistently:

1. current source and tests;
2. runtime knowledge generated from the current branch or working tree;
3. committed deterministic graph and generated Markdown;
4. human-curated domain and testing rules;
5. Wiki pages, issues, pull requests, memories, and historical sessions.

A curated rule that conflicts with current implementation is reported as a governance
conflict. It is not silently converted into an assertion about current behavior.

## Default-branch and feature-branch behavior

The committed pack is the shared default-branch baseline. Feature branches do not have
to publish every intermediate graph. The session-start hook can create a branch-local
runtime snapshot, which is ignored by Git and exists only for the current working
context. Once a behavior change is accepted, the deterministic baseline is regenerated
and reviewed in a normal pull request.

## Wiki role

The Wiki is a downstream, human-facing mirror. It is useful for browsing, onboarding,
and linking across teams, but agents should read same-repository knowledge files. This
avoids private-page fetch issues, stale web caches, and the ambiguity of whether a Wiki
is included in the repository's semantic index.
