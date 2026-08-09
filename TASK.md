# TASK.md — Working Protocol for DocuMesh

## Core Directives
1. **Never Bluff**: Claims must be grounded in source documents with exact verbatim quotes.
2. **Survive Crashes**: All graph steps checkpointed. Process death loses no completed work.
3. **Incremental Costing**: Adding 1 document updates affected register sections; does not re-process 1,000 docs.
4. **Human in the Loop**: Findings require human/MCP explicit approval before committing to final deliverable.
5. **Offline Testability**: Complete test suite runs without an API key using deterministic fallback extractors.

## Operational Conventions
- Use python3.13 / standard virtual environment.
- Modular code architecture under `src/`.
- Strict typing and Pydantic validation on all schemas.
