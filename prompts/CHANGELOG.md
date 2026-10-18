# Prompt changelog

## v1 (2026-10-16)
- Baseline: minimal instruction, schema enforced via structured output.

## v2 (2026-10-18)
- Added instruction not to add a trailing ".0" to numbers. `v1` left unchanged.
- "Never guess" now excepts `location.country`, which may be inferred from other address fields (matches the schema description).

## Schema updates (2026-10-18)
- `Location.country`: description now says to infer from other address fields when possible, else None.
- `RealEstateListing.name`: description now says property name only, None if not stated, never use the address as the name.
