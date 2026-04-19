# Tasks

## 1. Project Setup

- [x] 1.1 Initialize Python project with `uv` (pyproject.toml, `.python-version`
  pinned to 3.12)
- [x] 1.2 Add core dependencies: `dagster`, `dagster-webserver`, `dagster-dbt`,
  `dbt-postgres`, `fastapi`, `uvicorn`, `curl-cffi`, `beautifulsoup4`,
  `pdfplumber`, `pytesseract`, `pdf2image`, `Pillow`, `google-genai`,
  `sqlalchemy`, `sqlacodegen`, `psycopg2-binary`, `pydantic-settings`,
  `scalar-fastapi`
- [x] 1.3 Configure `prek` (`.pre-commit-config.yaml`) with ruff, mypy, uv lock
  check, and `dbt compile` check hooks
- [x] 1.4 Set up project directory structure: `ingestion/`, `extraction/`,
  `storage/`, `api/`, `dagster_pipeline/`, `dbt/`

## 2. Docker & Infrastructure

- [x] 2.1 Write `Dockerfile` for the application (ingestion + API in one image,
  Dagster jobs as separate entry points)
- [x] 2.2 Write `docker-compose.yml` with services: `db`
  (ghcr.io/kvdomingo/postgresql-pig:18), `dagster-webserver`,
  `dagster-daemon`, `api`
- [x] 2.3 Configure shared volume for PDF local storage (mounted into ingestion
  and API containers)
- [ ] 2.4 Set up Infisical project and populate secrets for dev environment
  (DATABASE_URL, GEMINI_API_KEY, PDF_STORAGE_PATH, etc.)
- [x] 2.5 Configure `infisical.json` (project ID + default environment) and
  document `infisical run --` usage in README

## 3. dbt Project (Pipeline Schemas)

- [x] 3.1 Initialize dbt project under `dbt/` with `dbt init`, configure
  `profiles.yml` to use the PostgreSQL service
- [x] 3.2 Define dbt seed for `psgc_boundaries` (psgc_code, name, region_code,
  level, alternative_names, geometry_wkt) and load with official PSGC data for
  NCR including WKT boundary geometries (EPSG:4326) from PSA PSGC dataset or
  equivalent (GADM/geoBoundaries)
- [x] 3.3 Define dbt source for raw ingestion tables (`source_documents`,
  `raw_extraction_results`) written by the Dagster ingestion assets
- [x] 3.4 Define dbt staging models to clean and normalise raw extraction output
- [x] 3.5 Define dbt intermediate models for PSGC resolution and price
  validation
- [x] 3.6 Define dbt mart model for `price_records` with table materialization,
  unique key `(effective_date, psgc_code, fuel_type)` for idempotent upserts,
  and appropriate indexes on `effective_date`, `psgc_code`, `fuel_type`
- [x] 3.7 Wire dbt project into Dagster via `dagster-dbt` (`DbtCliResource`,
  `@dbt_assets`) so dbt models run as Dagster assets downstream of ingestion
- [x] 3.8 Add a post-`dbt run` Dagster step that runs `sqlacodegen` and commits
  updated ORM models to `storage/models.py`
- [x] 3.9 Verify `dbt compile` passes in CI (prek hook)

## 4. DOE Ingestion Pipeline

- [x] 4.1 Implement robots.txt fetcher and path-allowance checker using
  `curl-cffi`
- [x] 4.2 Implement DOE article listing scraper (curl-cffi + BeautifulSoup) to
  extract PDF links and publication dates
- [x] 4.3 Implement polite HTTP wrapper: configurable per-request delay and
  exponential backoff with jitter
- [x] 4.4 Implement deduplication check against `source_documents` table (by
  URL)
- [x] 4.5 Implement PDF downloader: save binary to local storage path, compute
  content hash, register in `source_documents`
- [x] 4.6 Implement download retry logic: mark document as `download_failed`
  after retries exhausted
- [x] 4.7 Wrap scraping and download steps as Dagster assets with weekly
  schedule and weekly partitioning (starting December 2020)

## 5. PDF Extraction Pipeline

- [x] 5.1 Implement PDF type detector (digital vs. scanned) using `pdfplumber`
  text presence check
- [x] 5.2 Implement digital PDF text extractor using `pdfplumber`
- [x] 5.3 Implement scanned PDF renderer: PDF page → PIL Image via `pdf2image`
- [x] 5.4 Implement Tesseract OCR step for rendered page images; fall back to
  raw image path if OCR output is empty
- [x] 5.5 Implement Gemini API client: prompt Gemini with extracted text or page
  image to return a JSON array of
  `{fuel_type, price_php_per_liter, location_string, effective_date}` records
- [x] 5.6 Implement extraction cache: key Gemini results by content hash in the
  `source_documents` table; skip API call if cached result exists
- [x] 5.7 Write raw Gemini output to `raw_extraction_results` (dbt source table)
- [x] 5.8 Wrap extraction steps as Dagster assets downstream of the ingestion
  assets; dbt assets run after extraction to produce `price_records`

## 6. Storage Layer

- [x] 6.1 Run `sqlacodegen` against the database after `dbt run` to generate
  `storage/models.py`; commit generated models and re-run after any dbt schema
  change
- [x] 6.2 Implement document status update helper using the generated
  `SourceDocuments` model (called by ingestion and extraction Dagster assets)
- [x] 6.3 Implement query helpers using generated models: latest prices by
  region PSGC, price history by PSGC/fuel_type/date range

## 7. Price API

- [x] 7.1 Create FastAPI application with lifespan database connection
  management
- [x] 7.2 Replace default Swagger UI with Scalar (`scalar-fastapi` integration)
- [x] 7.3 Implement `GET /health` endpoint with database connectivity check
  (returns 503 if DB unreachable)
- [x] 7.4 Implement `GET /prices/latest` endpoint with `region` (PSGC code)
  query parameter
- [x] 7.5 Implement `GET /prices` endpoint with `region`, `fuel_type`, `from`,
  `to` (ISO 8601) query parameters
- [x] 7.6 Add Pydantic response models for price records, error responses, and
  health status
- [x] 7.7 Wire optional `Authorization: Bearer` middleware (disabled by default;
  enable via config for production rate-limiting)
- [x] 7.8 Verify Scalar docs accessible at `/docs` and raw OpenAPI spec at
  `/openapi.json`

## 8. Dagster Pipeline Wiring

- [x] 8.1 Define Dagster `Definitions` with all assets, schedules, and resources
  (DB connection, Gemini client, HTTP session, `DbtCliResource`)
- [x] 8.2 Register `@dbt_assets` so dbt models are visible and runnable in the
  Dagster UI, downstream of the extraction assets
- [x] 8.3 Configure weekly Dagster schedule (Friday) for the ingestion asset
- [x] 8.4 Configure weekly partition definition starting from 2020-12-01 for
  backfill support
- [ ] 8.5 Verify backfill can be triggered from Dagster UI for a sample date
  range

## 9. Testing

- [x] 9.1 Collect 5–10 representative historical DOE PDFs as fixtures (mix of
  digital and scanned, various years)
- [x] 9.2 Write unit tests for robots.txt checker and polite HTTP wrapper
- [x] 9.3 Write unit tests for PDF type detector and text extractor
- [x] 9.4 Write dbt tests (schema tests + custom data tests) for staging,
  intermediate, and mart models including PSGC resolution and price range checks
- [x] 9.5 Write integration tests for end-to-end extraction pipeline using
  fixture PDFs (mock Gemini API responses)
- [x] 9.6 Write API tests for all endpoints using a test database
- [ ] 9.7 Run end-to-end pipeline against live DOE site for the most recent
  publication and verify stored records match published prices
