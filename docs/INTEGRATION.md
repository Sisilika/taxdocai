# Integration Notes: Mock Connector → Real Tax-Prep Software

Drake Tax and UltraTax CS don't expose public developer APIs, so this project
ships a **mock connector** (`backend/app/routers/export.py`) that exports
reviewed documents as CSV and XML instead. This document explains how that
stub maps to what a real integration would look like.

## What the mock does
- `/api/export/csv/{document_id}` — flat CSV: one row per extracted box/field
- `/api/export/xml/{document_id}` — nested XML matching a generic
  `<TaxDocument><Fields><Field>...` shape

## How this maps to real integrations

**Drake Tax** supports importing client data via its proprietary `.DRK` file
format and a "GruntWorx"-style document import pipeline for scanned source
docs. A real integration would:
1. Map our `ExtractedDocument` schema fields to Drake's specific input-screen
   field codes (e.g. W-2 Box 1 → Drake's "W2:line 1" field reference).
2. Replace our generic XML export with Drake's documented import schema
   (requires a Drake reseller/developer agreement to access).
3. Likely run as a desktop-side plugin or scheduled import job rather than a
   pure REST call, since Drake is largely a desktop application.

**UltraTax CS (Thomson Reuters)** offers a "SourceLink"/data-sharing
mechanism and supports importing via their proprietary `.xfo`/CSV bridge
files for trial balance and K-1 data. A real integration would:
1. Match our schema to UltraTax's field IDs (available via their developer
   partner program).
2. Generate the bridge file format UltraTax expects on import, rather than
   our generic XML.
3. Handle UltraTax's per-client file structure (each return is a discrete
   file on disk in their data path).

## Why CSV/XML as the stand-in
Both target systems are desktop-first and import-driven rather than
API-driven, so a flat, well-typed export (CSV/XML) is actually the realistic
shape of *any* integration here — the main engineering work in a real
deployment would be the field-mapping table, not a live API client. The
`ExtractedDocument` Pydantic schema in this project is intentionally generic
so that mapping table is a thin, swappable layer.
