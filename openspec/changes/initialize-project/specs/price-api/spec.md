# Price API

## ADDED Requirements

### Requirement: Query latest fuel prices

The system SHALL provide an API endpoint that returns the most recent available
price for each fuel type in a given region.

#### Scenario: Latest NCR prices requested

- **WHEN** a client sends `GET /prices/latest?region=NCR`
- **THEN** the API SHALL return a JSON list of the most recent price record per
  fuel type for NCR, including `fuel_type`, `price_php_per_liter`,
  `effective_date`, and `region`

#### Scenario: Region has no data

- **WHEN** a client requests latest prices for a region with no stored records
- **THEN** the API SHALL return HTTP 404 with a descriptive error message

### Requirement: Query historical fuel prices by date range

The system SHALL provide an API endpoint to retrieve price records within a
specified date range, filterable by region and fuel type.

#### Scenario: Date range query with fuel type filter

- **WHEN** a client sends
  `GET /prices?region=NCR&fuel_type=diesel&from=2025-01-01&to=2025-03-31`
- **THEN** the API SHALL return all matching price records ordered by
  `effective_date` ascending

#### Scenario: Date range with no matching records

- **WHEN** a client queries a date range for which no records exist
- **THEN** the API SHALL return HTTP 200 with an empty list

#### Scenario: Invalid date format supplied

- **WHEN** a client supplies a `from` or `to` parameter that is not a valid ISO
  8601 date
- **THEN** the API SHALL return HTTP 422 with a field-level validation error

### Requirement: Expose OpenAPI documentation

The system SHALL automatically generate and serve an OpenAPI 3.x specification
for the price API.

#### Scenario: OpenAPI spec accessible

- **WHEN** a client sends `GET /docs` or `GET /openapi.json`
- **THEN** the server SHALL return the generated OpenAPI documentation without
  authentication

### Requirement: Optional API key authentication

The API SHALL be publicly accessible without authentication in the POC. The
middleware layer SHALL accept an optional `Authorization: Bearer <key>` header
so that API key enforcement can be enabled for rate-limiting in production
without a breaking change to existing unauthenticated clients.

#### Scenario: Request without API key (POC mode)

- **WHEN** a client sends a request with no `Authorization` header and the
  service is configured with authentication disabled
- **THEN** the API SHALL process the request normally

#### Scenario: Request with valid API key (production mode)

- **WHEN** a client sends a request with a valid `Authorization: Bearer <key>`
  header and the service is configured with authentication enabled
- **THEN** the API SHALL process the request normally

#### Scenario: Request with invalid API key (production mode)

- **WHEN** a client sends a request with an unrecognised or malformed
  `Authorization` header and authentication is enabled
- **THEN** the API SHALL return HTTP 401

### Requirement: Health check endpoint

The system SHALL expose a health check endpoint for liveness probing.

#### Scenario: Service is healthy

- **WHEN** a client sends `GET /health`
- **THEN** the API SHALL return HTTP 200 with `{"status": "ok"}` and SHALL
  verify database connectivity as part of the check

#### Scenario: Database unreachable

- **WHEN** the health check runs and the database connection fails
- **THEN** the API SHALL return HTTP 503 with
  `{"status": "degraded", "detail": "<error message>"}`
