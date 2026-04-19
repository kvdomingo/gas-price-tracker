# Price Storage

## ADDED Requirements

### Requirement: Store structured fuel price records keyed by PSGC codes

The system SHALL persist validated fuel price records in PostgreSQL using PSGC
(Philippine Standard Geographic Code) admin boundary codes as the canonical
identifiers for region and city/municipality, rather than raw name strings.

#### Scenario: New price record inserted

- **WHEN** a validated price record is received from the extraction layer with a
  resolved PSGC code
- **THEN** the system SHALL insert a row with fields `effective_date`,
  `psgc_code`, `fuel_type`, `price_php_per_liter`, `source_document_id`, and
  `ingested_at` timestamp

#### Scenario: Duplicate record detected

- **WHEN** a price record for the same `effective_date`, `psgc_code`, and
  `fuel_type` already exists
- **THEN** the system SHALL skip the insert and log a debug message, leaving the
  existing record unchanged (idempotent upsert)

### Requirement: PSGC lookup table with admin boundary geometries

The system SHALL maintain a `psgc_boundaries` reference table mapping PSGC codes
to canonical names, region hierarchy, alternative name variants, and admin
boundary geometry (stored as WKT text), to allow location resolution now and
spatial queries after a future PostGIS migration.

#### Scenario: Raw location string resolved to PSGC code

- **WHEN** the extraction layer receives a raw location string (e.g., "Makati
  City" or "City of Makati")
- **THEN** the system SHALL look up a matching PSGC code from the reference
  table and use it as the location identifier

#### Scenario: Raw location string cannot be resolved

- **WHEN** a raw location string does not match any entry in the PSGC lookup
  table
- **THEN** the system SHALL store the record with a null `psgc_code`, store the
  raw string in a `raw_location` field, and flag the record for manual
  resolution

#### Scenario: Boundary geometry present in seeded data

- **WHEN** the `psgc_boundaries` table is seeded
- **THEN** each row SHALL include a `geometry_wkt` column containing the
  MultiPolygon boundary in WKT format (EPSG:4326), or NULL if no boundary data
  is available for that administrative level

### Requirement: Track ingestion document metadata

The system SHALL maintain a `source_documents` table recording each downloaded
PDF's URL, local path, content hash, download timestamp, and processing status.

#### Scenario: Document registered on download

- **WHEN** a new PDF is downloaded
- **THEN** the system SHALL insert a row in `source_documents` with
  `status = 'downloaded'` and compute and store the file's content hash

#### Scenario: Document status updated after extraction

- **WHEN** extraction completes (successfully or with errors)
- **THEN** the system SHALL update the document's status to one of `extracted`,
  `extraction_failed`, or `validation_error`

### Requirement: Support region-scoped queries via PSGC hierarchy

The price record schema SHALL support filtering by region using the PSGC
hierarchy (region → province → city/municipality), so that queries for "NCR"
return all city-level records within NCR.

#### Scenario: Region-level query

- **WHEN** the storage layer is queried with a region-level PSGC code (e.g.,
  NCR's PSGC code `130000000`)
- **THEN** the system SHALL return all price records whose `psgc_code` belongs
  to that region's hierarchy
