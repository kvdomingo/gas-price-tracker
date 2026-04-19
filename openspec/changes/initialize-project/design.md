# Design

## Context

The DOE publishes weekly retail fuel pump prices for the Philippines via a web
listing at doe.gov.ph, with publications going back to December 2020. Each entry
links to a PDF. These PDFs are inconsistent: some are digitally generated
(selectable text), while others are scanned image documents. There is no
official API or structured data export.

This project is a greenfield POC focused on NCR prices, designed to extend to
all regions without breaking changes. Region and city identifiers will use
Philippine Standard Geographic Code (PSGC) codes to remain stable regardless of
how location names are written across publications.

## Goals / Non-Goals

**Goals:**

- Discover and download new weekly DOE price publications automatically, with
  polite HTTP behavior
- Extract tabular price data from both digital and image-scanned PDFs using a
  two-pass strategy with AI-assisted interpretation
- Store cleaned records keyed by PSGC codes in a queryable PostgreSQL schema
- Expose a minimal read API (FastAPI + Scalar docs) for latest and historical
  prices
- Orchestrate the pipeline with Dagster for observability, scheduling, and
  backfill support
- Design data models that can extend to all regions without schema changes

**Non-Goals:**

- Real-time or intraday price tracking (DOE data is weekly)
- Price forecasting or analytics beyond raw data storage
- Non-NCR regions in the initial POC
- A consumer-facing UI (API only for POC)
- Handling non-fuel commodities from DOE

## Decisions

### 1. Pipeline orchestration: Dagster

**Decision**: Use Dagster to define, schedule, and monitor the ingestion and
extraction pipeline.

**Rationale**: Dagster provides built-in scheduling, asset-based lineage
tracking, and a UI for inspecting runs and retries. It naturally models the
pipeline stages (scrape → download → extract → load) as assets with
dependencies, making backfills (e.g., December 2020 to present) trivial via
Dagster's partition and backfill system. This replaces a hand-rolled APScheduler
cron.

**Alternatives considered**:

- APScheduler + manual retry logic: no lineage, no UI, no built-in backfill
  support
- Airflow: heavier operational footprint for a single-pipeline project
- Prefect: comparable to Dagster; Dagster's asset model fits the DOE ingestion
  flow more naturally

### 2. PDF extraction strategy: pdfplumber + Tesseract OCR + Gemini AI interpretation

**Decision**: Use `pdfplumber` for digital PDFs. For image-scanned PDFs, render
pages to images and run Tesseract OCR. For both paths, pass the raw extracted
text (or page image for scanned PDFs) to Gemini (via Google Generative AI SDK)
to interpret and return a structured price table as JSON.

**Rationale**: The DOE table layout varies across publications and officers. A
rigid regex/column-index parser breaks on any layout change. Using Gemini as the
interpretation layer handles layout variation, OCR noise, and header ambiguity
without requiring per-publication rule updates. Gemini receives either the
extracted text (digital path) or the page image (scanned path) and returns a
canonical JSON array of price records.

**Alternatives considered**:

- Pure regex/column-index parser: brittle against layout changes and OCR noise
- Claude (Anthropic API): viable multimodal option but Google ecosystem is
  preferred given Gemini's strong document understanding capabilities
- Structured output prompt with GPT-4o: adds an OpenAI dependency

### 3. HTTP client: curl-cffi with rate limiting and robots.txt compliance

**Decision**: Use `curl-cffi` for all HTTP requests to the DOE website, with
per-request delays, exponential backoff on failure, and robots.txt checking
before any scraping begins.

**Rationale**: `curl-cffi` impersonates a real browser's TLS fingerprint, making
the scraper more resilient to any future bot-detection measures the DOE site may
adopt. The DOE site is rudimentary with no apparent crawler protection, but
polite behavior (delays, backoff, robots.txt) is the correct default regardless.

**Alternatives considered**:

- httpx: standard async client, but no TLS fingerprint impersonation
- Playwright/Selenium: too heavy for a site that appears to be server-rendered
  HTML

### 4. Region and city identifiers: PSGC codes with admin boundary geometries

**Decision**: Use PSGC codes as canonical location identifiers and seed the
`psgc_boundaries` table with both metadata and GeoJSON/WKT admin boundary
geometries sourced from the PSA's official PSGC dataset or an equivalent open
boundary dataset (e.g., GADM, geoBoundaries).

**Rationale**: DOE publications inconsistently name locations (e.g., "Makati
City" vs. "City of Makati"). PSGC codes decouple storage from naming
variability. Storing boundary geometries now — even as plain `text`/`jsonb`
in the POC — costs nothing extra at seed time and avoids a data backfill when
a map UI or spatial queries are added later.

**Alternatives considered**:

- Store raw name strings: cheap but creates duplicate/inconsistent records
- Normalize to a fixed naming convention: fragile against future DOE formatting
  changes
- Store geometries only when needed: forces a costly retroactive data fetch
  and migration

### 5. Schema management: dbt for pipeline tables, Alembic for golden/API tables

**Decision**: Split schema ownership between two tools:

- **dbt** (via `dagster-dbt`) manages all pipeline-internal tables: raw
  ingestion staging, intermediate extraction results, and the `psgc_boundaries`
  reference seed. These schemas are defined as dbt models/seeds and materialized
  by Dagster as assets.
- **Alembic** manages only the golden tables consumed by the FastAPI service
  (i.e., `price_records` and any API-specific views). Alembic migrations are
  applied as a deployment step before the API starts.

**Rationale**: dbt is the natural owner of transformation logic and its schemas.
Coupling intermediate table shapes to Alembic migrations creates unnecessary
churn during pipeline iteration. Alembic is reserved for the stable, public
contract that the API exposes — changes there are infrequent and warrant the
formalism of versioned migrations.

**Alternatives considered**:

- Alembic for everything: tight coupling between pipeline iteration and
  migration history; makes rapid schema experimentation slow
- dbt for everything including golden tables: the API layer then has no
  migration safety net for its schema contract

### 6. Data store: PostgreSQL (TimescaleDB + PostGIS migration path)

**Decision**: Use the custom `ghcr.io/kvdomingo/postgresql-pig:18` PostgreSQL
image. No TimescaleDB or PostGIS extensions in the POC, but the schema is
explicitly designed to enable both without breaking changes:

- `price_records.effective_date` is the natural time-series dimension; the
  table can be converted to a TimescaleDB hypertable partitioned on this column
  with a single `create_hypertable()` call
- `psgc_boundaries.geometry_wkt` is stored as `text` (WKT) in the POC; the
  column can be migrated to PostGIS `geometry(MultiPolygon, 4326)` by enabling
  the extension and running `ALTER COLUMN … TYPE geometry USING
  ST_GeomFromText(…)`

**Rationale**: Plain PostgreSQL is sufficient for POC volume. Storing geometry
as WKT text now means no re-seeding is required when PostGIS is enabled. The
TimescaleDB migration path is trivial if query latency becomes a concern at
nationwide scale.

### 7. API: FastAPI + Scalar

**Decision**: Use FastAPI with Pydantic v2 models. Replace the default Swagger
UI with Scalar for API documentation.

**Rationale**: FastAPI provides automatic OpenAPI spec generation, async
support, and type-safe models with minimal boilerplate. Scalar is a modern
drop-in replacement for Swagger UI with better UX and no additional backend
changes needed.

### 8. Secret management: Infisical

**Decision**: Use Infisical for all secret management. Secrets are injected at
runtime via `infisical run --` and never stored in `.env` files or the
repository.

**Rationale**: Centralised secret management with audit trails and
per-environment scoping (dev/prod) without committing credentials or maintaining
`.env` files. The Infisical CLI integrates cleanly with Docker Compose via the
`infisical run --` prefix.

**Alternatives considered**:

- `.env` files: simple but leak risk, no audit trail, per-developer drift
- Docker secrets: suited for Swarm/Kubernetes, not bare Compose

### 9. Containerization: Docker Compose

**Decision**: Define all services (PostgreSQL, Dagster webserver, Dagster
daemon, FastAPI) in a `docker-compose.yml`.

**Rationale**: Keeps local development and deployment consistent. Dagster
requires separate webserver and daemon processes; Docker Compose is the natural
way to manage these alongside the database.

## Risks / Trade-offs

- **DOE site structure changes** → Scraper breaks if article listing HTML
  changes. Mitigation: store raw HTML alongside downloads; alert if zero new
  documents are found after a run.
- **AI interpretation cost and latency** → Each PDF page sent to Gemini incurs
  API cost and adds latency to the pipeline. Mitigation: cache extraction
  results against the source document hash; only re-run AI interpretation if the
  document changes.
- **OCR quality on degraded scans** → Old scanned PDFs may produce garbled text
  that confuses the AI. Mitigation: store the raw OCR text alongside the AI
  output; flag records where Gemini returns low-confidence or empty results for
  manual review.
- **PSGC code mapping coverage** → Some DOE location strings may not map cleanly
  to a PSGC code. Mitigation: store the raw location string alongside the
  resolved PSGC code; unmapped strings are flagged and stored with a null PSGC
  reference for later resolution.
- **Backfill volume** → December 2020 to present is ~4+ years of weekly
  publications. Mitigation: Dagster's partition-based backfill lets this run
  incrementally without overwhelming the DOE site; rate limiting and delays
  apply to the backfill as well.

## Migration Plan

This is a greenfield project; no migration from existing systems is required.

Deployment steps:

1. Build and push Docker images
2. Start PostgreSQL via Docker Compose and apply Alembic migrations
3. Start Dagster webserver and daemon
4. Trigger historical backfill (December 2020 → present) via Dagster UI
5. Confirm records appear in database and API responds correctly
6. Enable the weekly Dagster schedule for ongoing ingestion

Rollback: all services are stateless containers; roll back to a previous image
tag. Database schema changes use versioned Alembic migrations.

## Resolved Questions

- **API authentication**: The API is open (no key required) for the POC. The
  FastAPI middleware layer SHALL be designed to accept an optional
  `Authorization` header so API key enforcement can be added for rate-limiting
  in production without a breaking change to existing clients.
- **Historical DOE data access**: All historical publications (back to December
  2020) are publicly accessible without authentication.
