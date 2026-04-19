# DOE Ingestion

## ADDED Requirements

### Requirement: Respect robots.txt before scraping

The system SHALL fetch and parse the DOE website's `robots.txt` before making
any scraping requests, and SHALL NOT request any path disallowed for the
configured user agent.

#### Scenario: Path allowed by robots.txt

- **WHEN** the ingestion job starts and the target article listing path is not
  disallowed in `robots.txt`
- **THEN** the system SHALL proceed with scraping normally

#### Scenario: Path disallowed by robots.txt

- **WHEN** the ingestion job starts and the target path is disallowed for the
  configured user agent
- **THEN** the system SHALL abort the run, log a warning, and take no further
  action

### Requirement: Discover new DOE fuel price publications

The system SHALL scrape the DOE article listing page using `curl-cffi` to
discover new weekly fuel price PDF publications. The system SHALL compare
discovered publication URLs against already-ingested records to identify new
documents only.

#### Scenario: New publication available

- **WHEN** the ingestion job runs and a PDF link is found that has not been
  previously ingested
- **THEN** the system SHALL queue the PDF URL for download

#### Scenario: No new publications

- **WHEN** the ingestion job runs and all discovered PDF links already exist in
  the ingested records
- **THEN** the system SHALL complete the run as a no-op without re-downloading
  any documents

#### Scenario: DOE listing page unreachable

- **WHEN** the ingestion job runs and the DOE listing page returns a non-2xx
  HTTP status or times out
- **THEN** the system SHALL apply exponential backoff and retry up to a
  configurable maximum (default: 3 retries), then log the error and skip the run
  without crashing

### Requirement: Polite HTTP behavior

All HTTP requests to the DOE website SHALL include a configurable delay between
requests and SHALL apply exponential backoff with jitter on failure, to avoid
overloading the DOE server.

#### Scenario: Sequential requests with delay

- **WHEN** the ingestion job makes multiple HTTP requests to the DOE website
- **THEN** each request SHALL be preceded by a configurable delay (default: 1
  second minimum)

#### Scenario: Request failure triggers backoff

- **WHEN** an HTTP request to the DOE website fails with a 5xx status or network
  error
- **THEN** the system SHALL wait for an exponentially increasing delay with
  jitter before retrying, up to the configured retry limit

### Requirement: Download and store raw PDF documents

The system SHALL download each newly discovered PDF and store it locally before
processing, so that re-extraction can be performed without re-fetching from the
DOE website.

#### Scenario: Successful PDF download

- **WHEN** a new publication URL is identified
- **THEN** the system SHALL download the PDF binary, save it to a configurable
  local storage path, and record the download timestamp and source URL in the
  database

#### Scenario: Download failure after retries exhausted

- **WHEN** a PDF download fails on all retry attempts
- **THEN** the system SHALL log the error and mark the publication as
  `download_failed` so it can be retried on the next run

### Requirement: Scheduled and backfill-capable ingestion

The system SHALL run the ingestion pipeline on a weekly schedule via Dagster,
and SHALL support partition-based backfills to ingest historical publications
from December 2020 onwards.

#### Scenario: Scheduled weekly run

- **WHEN** the Dagster schedule fires (weekly, aligned with DOE's Friday
  publication cadence)
- **THEN** the system SHALL automatically invoke discovery and download for the
  current week

#### Scenario: Historical backfill triggered

- **WHEN** an operator triggers a Dagster backfill for a date range starting
  from December 2020
- **THEN** the system SHALL process each weekly partition in order, applying the
  same polite scraping behavior as a live run
