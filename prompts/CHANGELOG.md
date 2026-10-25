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

## Schema update (2026-10-25)
- `Location.state`: state, province, or region. Description now says to use an ISO 3166-2 code.
- `Location.country`: country, inferred from other address fields when possible, otherwise None. Description now says to use an ISO 3166-1 alpha-2 code.
- `RealEstateListing.floors_total`: total number of floors (sometimes called stories). New description; if the total is not stated, check the Floor Plans section when available.
- `RealEstateListing.condition`: building condition, inferred from content when not stated explicitly. Description now says to fall back to `unknown` when nothing matches.

## Golden set v4 (2026-10-25)
- New `data/golden_v4.json`, based on `golden_v3.json` (same 10 documents). Use with `--golden-version v4`.
- `location.country` is `US` on every listing, replacing `USA`, to match the ISO 3166-1 alpha-2 schema.
- Amenities filled or expanded where v3 was empty, a placeholder, or incomplete: `gs02` (parking), `gs04` (replaced `"string"`), `gs05`, `gs06` (courtyard, atrium, rooftop, pool, green roof), `gs7` (yard, docks, power, clear height), `gs8` (utilities and frontage), `gs10` (gallery, structure, storage, garden).
- `floors_total` set where the brochure states it: `gs04` 2, `gs05` 1, `gs06` 20. `gs10` `condition` set to `unknown`.
- Sellers normalized: Colliers team credit shortened to `Colliers` on `gs02`–`gs04`; `gs05` seller typo corrected to `Commercial Asset Advisors`.

## v4 (2026-10-25)
- Added instruction that price-related fields are usually in a "Pricing & Financial Summary" section, or a similarly named section. `v1`–`v3` left unchanged.
