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

## Schema update (2026-10-20)
- `RealEstateListing.name`: description adds that the name can be near the address on the first page.
- `RealEstateListing.type_other`: description now says it is the raw property type value after mapping to the `type` enum.
- `TotalPrice.amount`: description adds "AKA asking price for the listed property."
- `RealEstateListing.condition`: new description; if not specified explicitly, infer from content.
- `PropertySize.sf`: description adds "Aka Lot size."

## v3 (2026-10-20)
- "Never guess" now also excepts `condition`, which may be inferred from content when not stated explicitly (matches the schema description). `v1` and `v2` left unchanged.
- Added instruction to ignore "Opportunity" and "Comparables" sections and focus on details about the listed property.

## Schema update (2026-10-21)
- `RealEstateListing.type`: description adds "Actual type of the listed property."
- `RealEstateListing.total_price`: new description "Asking price."

## Golden set v3 (2026-10-21)
- New `data/golden_v3.json`, copied from `golden_v2.json`. `gs01` (33 Unit Multifamily Development): added the missing `amenities` (washer/dryer hookups, patio/balcony, 9-10 foot ceilings, covered parking, fully enclosed building, elevator). Use with `--golden-version v3`.
