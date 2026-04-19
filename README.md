# PH Fuel Price Tracker

A data pipeline and API for tracking weekly retail fuel pump prices in the
Philippines, sourced from the Department of Energy's public publications.

This project also serves as an experiment in spec-driven development using
[OpenSpec](https://openspec.dev) to improve AI-assisted workflow — from
structured proposals and technical design through to implementation tasks.

## Overview

The DOE publishes weekly fuel price data going back to December 2020, but only
as PDFs — some digitally generated, others image-scanned. This project automates
the full pipeline from discovery to query:

1. **Ingest** — scrapes the DOE article listing weekly using `curl-cffi` with
   polite rate limiting, robots.txt compliance, and exponential backoff
2. **Extract** — detects PDF type (digital vs. scanned), runs `pdfplumber` or
   Tesseract OCR accordingly, then uses the Claude API to interpret the raw
   content into structured price records
3. **Store** — persists validated records in PostgreSQL keyed by
   [PSGC](https://psa.gov.ph/classification/psgc) admin boundary codes for
   stable, name-agnostic location identity
4. **Serve** — exposes a FastAPI + Scalar read API for querying current and
   historical prices by region, fuel type, and date range

Initial scope is NCR (National Capital Region). The schema and pipeline are
designed for nationwide expansion.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 + uv |
| Orchestration | Dagster |
| HTTP | curl-cffi |
| PDF extraction | pdfplumber + Tesseract OCR |
| AI interpretation | Gemini API (Google) |
| Database | PostgreSQL (`ghcr.io/kvdomingo/postgresql-pig:18`) |
| API | FastAPI + Scalar |
| Secrets | Infisical |
| Infrastructure | Docker Compose |
| Hooks | Prek |

## Getting Started

> Prerequisites: Docker, Docker Compose, and access to the project's Infisical
> workspace (which holds `DATABASE_URL`, `GOOGLE_API_KEY`, etc.). Install the
> [Infisical CLI](https://infisical.com/docs/cli/overview) and authenticate
> before running any commands.

```bash
infisical login
infisical run -- docker compose up -d
```

Apply database migrations:

```bash
infisical run -- docker compose exec api alembic upgrade head
```

Seed PSGC boundary data:

```bash
infisical run -- docker compose exec api python -m storage.seed_psgc
```

Trigger a manual ingestion run (or use the Dagster UI at
`http://localhost:3000`):

```bash
infisical run -- docker compose exec dagster-daemon python -m ingestion.cli run
```

The API is available at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

## Data Source

Weekly retail pump prices published by the Philippine Department of Energy:
<https://doe.gov.ph/articles/group/liquid-fuels?category=Retail%20Pump%20Prices&display_type=Card>

Historical publications are available from December 2020 onwards.
