# Agent operating guide

## Project

This is a zero-dependency Python demo of a shared, fresh, Copilot-readable knowledge loop for test generation.

## Commands

- `make test` — run the unit tests.
- `make knowledge` — regenerate the committed code graph and knowledge projection.
- `make freshness` — compare source inputs with the committed manifest.
- `make check` — verify tests, freshness, and deterministic generated output.
- `make context` — prepare branch-aware runtime knowledge.
- `make query SYMBOL=PaymentService.authorize` — query a narrow graph slice.
- `make wiki-export` — build a flat human-facing Wiki mirror in `dist/wiki`.

## Rules

- Current source code is authoritative.
- Runtime branch knowledge outranks committed baseline knowledge.
- Generated files are outputs, not editing targets.
- Shared Agent sessions provide provenance; committed repository files provide agent-to-agent handoff.
- Wiki pages are a human portal, not the primary Agent context.
