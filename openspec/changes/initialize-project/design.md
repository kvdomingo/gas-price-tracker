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

### 2. PDF extraction strategy: pdfplumber + Tesseract OCR + Claude AI interpretation

**Decision**: Use `pdfplumber` for digital PDFs. For image-scanned PDFs, render
pages to images and run Tesseract OCR. For both paths, pass the raw extracted
text (or page image for scanned PDFs) to Claude (via Anthropic API) to interpret
and return a structured price table as JSON.

**Rationale**: The DOE table layout varies across publications and officers. A
rigid regex/column-index parser breaks on any layout change. Using Claude as the
interpretation layer handles layout variation, OCR noise, and header ambiguity
without requiring per-publication rule updates. Claude receives either the
extracted text (digital path) or the page image (scanned path) and returns a
canonical JSON array of price records.

**Alternatives considered**:

- Pure regex/column-index parser: brittle against layout changes and OCR noise
- Google Cloud Vision API for OCR: higher cost, external data dependency
- Structured output prompt with GPT-4o: viable but adds an OpenAI dependency
  when Anthropic is preferred

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

### 4. Region and city identifiers: PSGC codes

**Decision**: Use Philippine Standard Geographic Code (PSGC) codes as the
canonical identifiers for regions and cities in the database schema and API.

**Rationale**: DOE publications inconsistently name locations (e.g., "Makati
City" vs. "City of Makati"). PSGC codes are stable government identifiers that
decouple storage from naming variability. A lookup table maps PSGC codes to
display names; the extraction step resolves location strings to PSGC codes
before storage.

**Alternatives considered**:

- Store raw name strings: cheap to implement but creates duplicate/inconsistent
  records
- Normalize to a fixed naming convention: fragile against future DOE formatting
  changes

### 5. Data store: PostgreSQL (`ghcr.io/kvdomingo/postgresql-pig:18`)

**Decision**: Use the custom `ghcr.io/kvdomingo/postgresql-pig:18` PostgreSQL
image. Schema managed with Alembic. No TimescaleDB for POC.

**Rationale**: Plain PostgreSQL with a date-indexed table is sufficient at this
data volume (weekly NCR data, ~52 rows/year per fuel type, with ~5 years of
history for backfill). The custom image is already available and familiar.
TimescaleDB can be adopted later if query performance warrants it.

### 6. API: FastAPI + Scalar

**Decision**: Use FastAPI with Pydantic v2 models. Replace the default Swagger
UI with Scalar for API documentation.

**Rationale**: FastAPI provides automatic OpenAPI spec generation, async
support, and type-safe models with minimal boilerplate. Scalar is a modern
drop-in replacement for Swagger UI with better UX and no additional backend
changes needed.

### 7. Containerization: Docker Compose

**Decision**: Define all services (PostgreSQL, Dagster webserver, Dagster
daemon, FastAPI) in a `docker-compose.yml`.

**Rationale**: Keeps local development and deployment consistent. Dagster
requires separate webserver and daemon processes; Docker Compose is the natural
way to manage these alongside the database.

## Risks / Trade-offs

- **DOE site structure changes** → Scraper breaks if article listing HTML
  changes. Mitigation: store raw HTML alongside downloads; alert if zero new
  documents are found after a run.
- **AI interpretation cost and latency** → Each PDF page sent to Claude incurs
  API cost and adds latency to the pipeline. Mitigation: cache extraction
  results against the source document hash; only re-run AI interpretation if the
  document changes.
- **OCR quality on degraded scans** → Old scanned PDFs may produce garbled text
  that confuses the AI. Mitigation: store the raw OCR text alongside the AI
  output; flag records where Claude returns low-confidence or empty results for
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

## Open Questions

- Should the API be key-protected or open for the POC?
- Do any historical DOE PDFs (pre-2022) require a login or are all publicly
  accessible?
