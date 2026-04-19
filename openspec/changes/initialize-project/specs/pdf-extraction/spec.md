# PDF Extraction

## ADDED Requirements

### Requirement: Detect PDF document type

The system SHALL detect whether a downloaded PDF contains embedded selectable
text or consists of scanned images, and route it to the appropriate extraction
method.

#### Scenario: Digital PDF detected

- **WHEN** a PDF is processed and contains embedded text on the relevant pages
- **THEN** the system SHALL use text-based extraction (pdfplumber) and SHALL NOT
  invoke Tesseract OCR

#### Scenario: Image-scanned PDF detected

- **WHEN** a PDF is processed and its pages contain no extractable text
- **THEN** the system SHALL render each page to a raster image and pass it
  through Tesseract OCR before AI interpretation

### Requirement: Extract raw content from digital PDF

The system SHALL extract raw text from digitally-generated PDFs using
`pdfplumber` and pass the extracted text to Claude AI for structured
interpretation.

#### Scenario: Text extracted from digital PDF

- **WHEN** a digital PDF is processed and text is extracted from the page
- **THEN** the system SHALL pass the raw text content to Claude AI for
  interpretation into structured price records

#### Scenario: No text found in digital PDF

- **WHEN** a digital PDF is processed but no text is found on any page
- **THEN** the system SHALL fall back to the image-scanned path (render → OCR →
  AI)

### Requirement: Extract raw content from image-scanned PDF via OCR

The system SHALL render image-scanned PDF pages to images and apply Tesseract
OCR to produce raw text, which is then passed to Claude AI for structured
interpretation.

#### Scenario: OCR produces text output

- **WHEN** Tesseract OCR runs on a rendered page image and produces non-empty
  text output
- **THEN** the system SHALL pass the OCR text to Claude AI for interpretation
  into structured price records

#### Scenario: OCR produces empty output

- **WHEN** Tesseract OCR runs but returns empty or whitespace-only output
- **THEN** the system SHALL pass the original page image directly to Claude AI
  (vision path) for interpretation

### Requirement: AI-assisted structured interpretation

The system SHALL use the Claude API to interpret raw extracted content (text or
image) into a canonical structured list of price records. Claude SHALL be
prompted to return a JSON array of price objects with defined fields.

#### Scenario: Claude returns well-formed structured output

- **WHEN** Claude is invoked with the extracted content and returns a valid JSON
  array of price records
- **THEN** the system SHALL parse the response and pass the records to the
  validation layer

#### Scenario: Claude returns empty or unparseable output

- **WHEN** Claude is invoked but returns an empty array or output that cannot be
  parsed as JSON
- **THEN** the system SHALL log a warning, mark the document as
  `extraction_failed`, and skip storage for that document

#### Scenario: Claude API unavailable

- **WHEN** the Claude API request fails due to a network error or rate limit
- **THEN** the system SHALL apply exponential backoff and retry up to a
  configurable limit before marking the document as `extraction_failed`

### Requirement: Cache AI extraction results

The system SHALL cache Claude's structured output keyed by the source document's
content hash, so that re-processing an unchanged document does not incur an
additional API call.

#### Scenario: Document previously processed

- **WHEN** the extraction step is triggered for a document whose content hash
  matches a cached extraction result
- **THEN** the system SHALL use the cached structured output and SHALL NOT call
  the Claude API again

#### Scenario: Document content changed

- **WHEN** the extraction step is triggered for a document whose content hash
  does not match any cached result
- **THEN** the system SHALL invoke Claude AI and store the new result in the
  cache

### Requirement: Validate extracted price records

The system SHALL validate each AI-interpreted price record to ensure it falls
within a plausible range before storage.

#### Scenario: Price within plausible range

- **WHEN** an extracted price record has a `price_php_per_liter` value between
  10 and 500 (configurable bounds)
- **THEN** the system SHALL accept the record and pass it to the storage layer

#### Scenario: Price outside plausible range

- **WHEN** an extracted price record has a `price_php_per_liter` value outside
  the configured bounds
- **THEN** the system SHALL reject the record, log it with the source document
  reference, and mark the document as `validation_error`
