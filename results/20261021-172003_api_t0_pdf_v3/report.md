# Run 20261021-172003_api_t0_pdf_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | pdf | v3 | v3 | 0.0 | 1.0 | 2 |

## Metrics

- Field accuracy: 83.9%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 19.5s / 32.6s
- Cost per 1000 docs: $8.44

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| type_other | 0 | 0 | 1 |
| amenities | 0 | 0 | 1 |
| name | 50 | 1 | 0 |
| type | 50 | 0 | 0 |
| price.per_sf | 50 | 0 | 0 |
| price.per_unit | 50 | 0 | 0 |
| seller | 50 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| price.per_sf_currency | 100 | 0 | 0 |
| price.per_unit_currency | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| total_price.amount | 100 | 0 | 0 |
| total_price.currency | 100 | 0 | 0 |
| total_price.period | 100 | 0 | 0 |
| size.sf | 100 | 0 | 0 |
| size.units | 100 | 0 | 0 |
| size.acreage | 100 | 0 | 0 |
| size.sqm | 100 | 0 | 0 |
| size.hectares | 100 | 0 | 0 |
| floor | 100 | 0 | 0 |
| floors_total | 100 | 0 | 0 |
| condition | 100 | 0 | 0 |
| location.city | 100 | 0 | 0 |
| location.state | 100 | 0 | 0 |
| location.country | 100 | 0 | 0 |
| location.zip | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | [] | ["Subterranean parking", "36 parking spaces"] |
| name | gs01_33 Unit Multifamily Development.pdf | 33 Unit Multifamily Development | null |
| price.per_sf | gs01_33 Unit Multifamily Development.pdf | 36.68 | 174.39 |
| price.per_unit | gs01_33 Unit Multifamily Development.pdf | 37879 | 167629 |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
| type_other | gs01_33 Unit Multifamily Development.pdf | Fully Entitled Development Land | Multifamily Development |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Multifamily |
