# Tasks

## 1. Project Setup

- [ ] 1.1 Initialize Python project with `uv` (pyproject.toml, `.python-version`
  pinned to 3.12)
- [ ] 1.2 Add core dependencies: `dagster`, `dagster-webserver`, `fastapi`,
  `uvicorn`, `curl-cffi`, `beautifulsoup4`, `pdfplumber`, `pytesseract`,
  `pdf2image`, `Pillow`, `anthropic`, `sqlalchemy`, `alembic`,
  `psycopg2-binary`, `pydantic-settings`, `scalar-fastapi`
- [ ] 1.3 Configure `prek` (`.pre-commit-config.yaml`) with ruff, mypy, and uv
  lock check hooks
- [ ] 1.4 Set up project directory structure: `ingestion/`, `extraction/`,
  `storage/`, `api/`, `migrations/`, `dagster_pipeline/`

## 2. Docker & Infrastructure

- [ ] 2.1 Write `Dockerfile` for the application (ingestion + API in one image,
  Dagster jobs as separate entry points)
- [ ] 2.2 Write `docker-compose.yml` with services: `db`
  (ghcr.io/kvdomingo/postgresql-pig:18), `dagster-webserver`,
  `dagster-daemon`, `api`
- [ ] 2.3 Configure shared volume for PDF local storage (mounted into ingestion
  and API containers)
- [ ] 2.4 Add `.env.example` documenting all required environment variables

## 3. Database Schema & Migrations

- [ ] 3.1 Initialize Alembic migration environment pointed at the PostgreSQL
  service
- [ ] 3.2 Create `psgc_boundaries` table migration (psgc_code PK, name,
  region_code, level, alternative_names JSONB)
- [ ] 3.3 Seed `psgc_boundaries` with official PSGC data for NCR
  cities/municipalities
- [ ] 3.4 Create `source_documents` table migration (id, url, local_path,
  content_hash, download_timestamp, effective_week, status)
- [ ] 3.5 Create `price_records` table migration (id, effective_date, psgc_code
  FK, fuel_type, price_php_per_liter, raw_location, source_document_id FK,
  ingested_at)
- [ ] 3.6 Add unique constraint on `(effective_date, psgc_code, fuel_type)`
- [ ] 3.7 Add indexes on `effective_date`, `psgc_code`, and `fuel_type`

## 4. DOE Ingestion Pipeline

- [ ] 4.1 Implement robots.txt fetcher and path-allowance checker using
  `curl-cffi`
- [ ] 4.2 Implement DOE article listing scraper (curl-cffi + BeautifulSoup) to
  extract PDF links and publication dates
- [ ] 4.3 Implement polite HTTP wrapper: configurable per-request delay and
  exponential backoff with jitter
- [ ] 4.4 Implement deduplication check against `source_documents` table (by
  URL)
- [ ] 4.5 Implement PDF downloader: save binary to local storage path, compute
  content hash, register in `source_documents`
- [ ] 4.6 Implement download retry logic: mark document as `download_failed`
  after retries exhausted
- [ ] 4.7 Wrap scraping and download steps as Dagster assets with weekly
  schedule and weekly partitioning (starting December 2020)

## 5. PDF Extraction Pipeline

- [ ] 5.1 Implement PDF type detector (digital vs. scanned) using `pdfplumber`
  text presence check
- [ ] 5.2 Implement digital PDF text extractor using `pdfplumber`
- [ ] 5.3 Implement scanned PDF renderer: PDF page → PIL Image via `pdf2image`
- [ ] 5.4 Implement Tesseract OCR step for rendered page images; fall back to
  raw image path if OCR output is empty
- [ ] 5.5 Implement Claude API client: prompt Claude with extracted text or page
  image to return a JSON array of
  `{fuel_type, price_php_per_liter, location_string, effective_date}`
  records
- [ ] 5.6 Implement extraction cache: key Claude results by content hash in the
  `source_documents` table; skip API call if cached result exists
- [ ] 5.7 Implement PSGC resolver: match raw `location_string` against
  `psgc_boundaries` (exact + fuzzy match on name and alternative_names);
  store `null` + raw string if unresolved
- [ ] 5.8 Implement price range validator: reject records outside configurable
  bounds (default 10–500 PHP/L)
- [ ] 5.9 Wrap extraction steps as Dagster assets downstream of the ingestion
  assets

## 6. Storage Layer

- [ ] 6.1 Implement SQLAlchemy ORM models for `psgc_boundaries`,
  `source_documents`, and `price_records`
- [ ] 6.2 Implement idempotent upsert for `price_records` (ON CONFLICT DO
  NOTHING)
- [ ] 6.3 Implement document status update helper (called by both ingestion and
  extraction Dagster assets)
- [ ] 6.4 Implement query helpers: latest prices by region PSGC, price history
  by PSGC/fuel_type/date range

## 7. Price API

- [ ] 7.1 Create FastAPI application with lifespan database connection
  management
- [ ] 7.2 Replace default Swagger UI with Scalar (`scalar-fastapi` integration)
- [ ] 7.3 Implement `GET /health` endpoint with database connectivity check
  (returns 503 if DB unreachable)
- [ ] 7.4 Implement `GET /prices/latest` endpoint with `region` (PSGC code)
  query parameter
- [ ] 7.5 Implement `GET /prices` endpoint with `region`, `fuel_type`, `from`,
  `to` (ISO 8601) query parameters
- [ ] 7.6 Add Pydantic response models for price records, error responses, and
  health status
- [ ] 7.7 Verify Scalar docs accessible at `/docs` and raw OpenAPI spec at
  `/openapi.json`

## 8. Dagster Pipeline Wiring

- [ ] 8.1 Define Dagster `Definitions` with all assets, schedules, and resources
  (DB connection, Claude client, HTTP session)
- [ ] 8.2 Configure weekly Dagster schedule (Friday) for the ingestion asset
- [ ] 8.3 Configure weekly partition definition starting from 2020-12-01 for
  backfill support
- [ ] 8.4 Verify backfill can be triggered from Dagster UI for a sample date
  range

## 9. Testing

- [ ] 9.1 Collect 5–10 representative historical DOE PDFs as fixtures (mix of
  digital and scanned, various years)
- [ ] 9.2 Write unit tests for robots.txt checker and polite HTTP wrapper
- [ ] 9.3 Write unit tests for PDF type detector and text extractor
- [ ] 9.4 Write unit tests for PSGC resolver (exact match, fuzzy match,
  unresolved case)
- [ ] 9.5 Write unit tests for price validator
- [ ] 9.6 Write integration tests for end-to-end extraction pipeline using
  fixture PDFs (mock Claude API responses)
- [ ] 9.7 Write API tests for all endpoints using a test database
- [ ] 9.8 Run end-to-end pipeline against live DOE site for the most recent
  publication and verify stored records match published prices
