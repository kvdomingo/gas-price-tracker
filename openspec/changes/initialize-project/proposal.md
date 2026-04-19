# Proposal

## Why

With ongoing geopolitical tensions in the Middle East driving fuel price
volatility, Filipino consumers and policymakers need timely, structured
visibility into weekly retail pump prices. The Department of Energy publishes
this data weekly — with archives going back to December 2020 — but only as
unstructured PDFs (sometimes image-scanned), making programmatic access
impossible without additional tooling.

## What Changes

- Introduce a Dagster-orchestrated pipeline that discovers, downloads, and
  extracts structured price data from weekly DOE PDF publications
- Use Claude AI to interpret extracted PDF content into structured records,
  handling layout variability and OCR noise
- Store cleaned records keyed by PSGC admin boundary codes in PostgreSQL for
  stable, region-consistent querying
- Expose a FastAPI + Scalar read API for querying current and historical NCR
  fuel prices
- Initial scope is NCR (National Capital Region) as POC, with schema designed
  for nationwide expansion

## Capabilities

### New Capabilities

- `doe-ingestion`: Discovers and downloads weekly fuel price PDF publications
  from the DOE website using curl-cffi with polite scraping behavior
- `pdf-extraction`: Extracts and interprets tabular price data from PDFs using a
  two-pass strategy (pdfplumber for digital PDFs, Tesseract OCR for scanned
  PDFs) with Claude AI for structured interpretation
- `price-storage`: Stores validated fuel price records keyed by PSGC codes in
  PostgreSQL, with idempotent upserts and document status tracking
- `price-api`: Exposes a FastAPI + Scalar API for querying current and
  historical NCR fuel prices by fuel type and date range

### Modified Capabilities

## Impact

- No existing code is affected; this is a greenfield project
- External dependencies: DOE public website (scraping), Anthropic API (AI
  extraction)
- Requires Docker for all services (PostgreSQL, Dagster, FastAPI)
- PSGC code lookup table required for location normalization; must be seeded
  before ingestion runs
- NCR-only scope for the POC; schema and pipeline must be designed to support
  nationwide expansion
