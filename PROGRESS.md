# PROGRESS.md — Assumptions & Decisions Log

## Architecture Decisions Log

### 1. Orchestration: LangGraph
- **Decision**: LangGraph state machine chosen over Agno/CrewAI.
- **Rationale**: Direct match with task brief's explicit preference; explicit node/edge state graph ensures visible stages; battle-tested PostgreSQL checkpointer guarantees crash survival.

### 2. Database & Search: SQLite / PostgreSQL Dual Driver
- **Decision**: Support SQLite (`sqlite-vss` / standard SQL) for local zero-config testing and PostgreSQL + `pgvector` for production RLS multi-tenancy.
- **Rationale**: Enables zero-setup single-command startup (`python -m src.cli run`) for reviewers without requiring local Postgres daemon.

### 3. Extraction & Grounding
- **Decision**: Two-pass extraction (schema-driven structured pass + unstructured fact pass) with Levenshtein fuzzy string quote-matching against source documents.
- **Rationale**: Prevents hallucinated figures; guarantees 100% citation precision.

### 4. Test Corpus & Planted Errors
- **Decision**: Built 8-document corpus (`Greenfield Tech Park`) in `test_data/` with 5 cross-document planted errors.
- **Answer Key**: Maintained in `test_data/SEED_CORPUS_KEY.md`.
