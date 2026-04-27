<!--
SYNC IMPACT REPORT
==================
Version change:      1.0.0 → 1.1.0 (MINOR — new principle VI added; tech stack fully specified)
Modified principles:
  II. Simplicity & YAGNI        — added MVP-first recommendation guidance (cosine similarity before ML)
  III. LLM-Aware Design         — clarified LLM is a conversation layer, not the recommendation core
  V. Conversational UX First    — added FSM-driven dialog design rule (aiogram 3 States)
Added sections:
  Principle VI. Ethical Scraping & External Dependency Management (new)
  Tech Stack updated with: aiogram 3, FastAPI, Redis, Celery + Beat, Playwright, Docker Compose
Removed sections:    None
Templates updated:
  ✅ .specify/templates/plan-template.md   — Constitution Check gates cover new Principle VI
  ✅ .specify/templates/spec-template.md   — no structural changes required
  ✅ .specify/templates/tasks-template.md  — scraper contract tasks and worker tasks now covered
Follow-up TODOs:     None.
-->

# Perfume Bot Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD is mandatory for all feature work:

- Tests MUST be written and confirmed failing before any implementation begins.
- The Red-Green-Refactor cycle MUST be followed without exception.
- Every user story MUST have at least one integration test covering its acceptance scenario.
- Unit tests cover pure logic; integration tests cover DB operations, Celery tasks, and API contracts.
- Scraper implementations MUST be tested against locally-saved HTML fixtures, never live sites in CI.
- No task is complete until its tests are green and the implementation is refactored.

**Rationale**: Defects caught during the Red phase cost near-zero to fix; defects caught in
production cost orders of magnitude more and erode user trust in a conversational product.

### II. Simplicity & YAGNI

Build only what the current user story requires:

- No abstraction MUST be introduced unless three concrete, present use-cases demand it.
- Dependencies MUST be justified: each new library must solve a problem that cannot be solved with
  the standard library or an already-present dependency.
- Recommendation engine MUST start as cosine similarity on note vectors; collaborative filtering
  or ML models MUST NOT be introduced until cosine similarity is live and validated with real users.
- Premature generalisation, speculative helpers, and unused exports are treated as defects and
  MUST be removed before a task is marked complete.

**Rationale**: A conversational bot grows incrementally. The market has no direct competitor yet —
the risk is shipping too late, not shipping too simply.

### III. LLM-Aware Design

The LLM is the conversational interface layer, not the recommendation core:

- The recommendation engine (note matching, price lookup) MUST be deterministic and testable
  without an LLM call; the LLM is responsible for natural-language framing of results only.
- Prompts MUST be versioned alongside code; changes to prompts require the same review as code.
- LLM calls MUST be wrapped in a single provider-abstraction layer so the underlying model can be
  swapped without touching business logic.
- Structured outputs (JSON schema validation) MUST be used wherever bot logic parses LLM responses.
- LLM latency and token cost MUST be logged per request to enable future optimisation.

**Rationale**: LLM behaviour changes with model upgrades and prompt drift; keeping it as a thin
presentation layer prevents cascading breakage in the recommendation and data pipeline.

### IV. Data Integrity

All persistent state MUST be managed with explicit, reversible migrations:

- Schema changes MUST be delivered as numbered Alembic migration files; no ad-hoc DDL outside
  migrations is permitted.
- Every entity written to the database MUST have a corresponding SQLAlchemy model; raw-dict
  insertion is forbidden.
- Price history MUST be append-only; no price record may be updated or deleted, only superseded
  by a new record with a later `checked_at` timestamp.
- Sensitive user data (preferences, conversation history) MUST NOT be logged at DEBUG level or
  above in production.

**Rationale**: Perfume preference data is personal; price history is the product's core value —
both must be reproducible and auditable.

### V. Conversational UX First

The user-facing response quality drives every implementation decision:

- Response latency MUST be under 3 seconds for 95% of bot interactions (p95 < 3 s).
- Every conversational flow MUST be modelled as an explicit aiogram 3 FSM (`StatesGroup`);
  free-form state held only in Redis is forbidden.
- The bot MUST handle ambiguous or incomplete input with a clarifying inline-keyboard prompt,
  never with a raw error message.
- All bot response copy (messages, button labels) MUST live in versioned template files, not
  hardcoded strings in handler code.
- Feature work MUST begin with the user story acceptance scenario and FSM state diagram, not the
  data model.

**Rationale**: A perfume advisor lives or dies on conversation quality; technical correctness
without a good user experience delivers no value.

### VI. Ethical Scraping & External Dependency Management

Scrapers are a critical but fragile dependency; they MUST be treated as first-class citizens:

- Scrapers MUST implement a minimum 1-second delay between requests to the same domain; no
  parallel requests to the same host are permitted.
- User-Agent rotation MUST be applied for all shop scrapers (Randewoo, Notino, Золотое Яблоко,
  Летуаль); a fixed User-Agent is a defect.
- Fragrantica catalog MUST be bootstrapped from a static dataset (e.g., the Kaggle Fragrantica
  dataset); live Playwright scraping of Fragrantica is permitted only for incremental updates,
  not bulk ingestion.
- Each scraper MUST implement a circuit breaker: if ≥ 5 consecutive requests to a domain fail
  or return non-200, the scraper MUST pause for at least 1 hour and emit a structured log event.
- Scraper contracts MUST be defined as an abstract base class with typed return signatures before
  any concrete scraper is implemented.
- The system MUST remain functional (with stale prices) when all scrapers are down; price data
  is a best-effort enhancement, not a hard dependency for the bot to respond.

**Rationale**: Scrapers can be blocked at any time; the product must degrade gracefully. Aggressive
scraping creates legal and reputational risk with no benefit.

## Technology Stack & Constraints

- **Language**: Python 3.11+
- **Bot framework**: aiogram 3 with FSM backed by Redis storage.
- **API backend**: FastAPI (async); exposes `/recommendations`, `/favorites`, `/prices` endpoints.
- **Database**: PostgreSQL (production); SQLite (local dev / CI). ORM: SQLAlchemy 2.x async.
  Migrations: Alembic with sequential numbered files.
- **Cache / message broker**: Redis — aiogram FSM state, API response cache, Celery broker.
- **Background workers**: Celery + Celery Beat.
  - `check_prices` task: every 6 hours, checks prices for all watched favorites.
  - `update_catalog` task: daily, incremental update from scraper sources.
  - `notify_users` task: triggered by `check_prices` when a price drops ≥ 10%.
- **Scraping**: Playwright (JS-heavy sites), httpx (static HTML shops).
- **Testing**: pytest + pytest-asyncio. Integration tests run against real SQLite; scraper tests
  use local HTML fixtures.
- **Deployment**: Docker Compose (all services in one compose file for local and staging).
- **Dependency management**: `pyproject.toml` + locked `requirements.txt`.
- **Secrets**: `.env` files only; never committed. All configuration via environment variables.

## Development Workflow

- Feature work follows the speckit workflow: `/speckit-specify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-implement`.
- Every feature branch is named `###-short-description` using sequential numbering.
- A Constitution Check MUST be performed at the start of every plan (`/speckit-plan`) and
  re-checked after the design phase.
- Pull requests require at least one passing CI run (lint + full test suite) before review.
- Commits MUST be atomic: one logical change per commit, with a message describing *why*, not *what*.
- Breaking changes to the LLM provider interface, the database schema, or the scraper base
  contract MUST be flagged in the PR description with a migration/rollback plan.
- Staged delivery order: MVP (bot + FSM + static catalog + cosine recommendations) → scrapers +
  real prices → Celery workers + notifications → Redis caching + catalog auto-update.

## Governance

This constitution supersedes all informal coding conventions and verbal agreements.

**Amendment procedure**:
1. Open a PR with the proposed change to `.specify/memory/constitution.md`.
2. The PR description MUST include: the principle affected, the motivation, and a migration plan
   for any in-flight work that relied on the previous wording.
3. Run `/speckit-constitution` after merge to propagate updates to dependent templates.

**Versioning policy** (semantic):
- MAJOR bump: backward-incompatible removal or redefinition of an existing principle.
- MINOR bump: new principle or section added; material expansion of existing guidance.
- PATCH bump: clarifications, wording, or typo fixes with no semantic change.

**Compliance review**: Every `/speckit-plan` Constitution Check is the enforcement point.
Violations that cannot be resolved MUST be documented in the plan's Complexity Tracking table
with a justification before work may proceed.

**Version**: 1.1.0 | **Ratified**: 2026-04-27 | **Last Amended**: 2026-04-27
