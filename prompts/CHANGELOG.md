# Prompt changelog

## v1 (2026-10-16)
- Baseline: minimal instruction, schema enforced via structured output.

## v2 (2026-10-18)
- Added instruction not to add a trailing ".0" to numbers. `v1` left unchanged.
- "Never guess" now excepts `location.country`, which may be inferred from other address fields (matches the schema description).

## Schema updates (2026-10-18)
- `Location.country`: description now says to infer from other address fields when possible, else None.
- `RealEstateListing.name`: description now says property name only, None if not stated, never use the address as the name.

## Schema update after v2 test run (2026-10-18)
- Numeric fields (`per_sf`, `per_unit`, `amount`, `sf`, `units`, `acreage`, `sqm`, `hectares`) changed from `float` to `int | float` so whole numbers no longer serialize as e.g. `37879.0`; the v2 prompt instruction alone did not prevent it.
