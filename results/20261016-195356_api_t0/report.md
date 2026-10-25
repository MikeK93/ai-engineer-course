# Run 20261016-195356_api_t0

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | text | v1 | v1 | 0.0 | 1.0 | 2 |

## Metrics

- Field accuracy: 76.8%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 8.6s / 15.2s
- Cost per 1000 docs: $7.54

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| type | 0 | 0 | 0 |
| size.units | 0 | 0 | 2 |
| amenities | 0 | 1 | 0 |
| location.country | 0 | 2 | 0 |
| name | 50 | 0 | 1 |
| total_price.amount | 50 | 0 | 0 |
| size.sf | 50 | 0 | 0 |
| location.zip | 50 | 0 | 1 |
| seller | 50 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| type_other | 100 | 0 | 0 |
| price.per_sf | 100 | 0 | 0 |
| price.per_sf_currency | 100 | 0 | 0 |
| price.per_unit | 100 | 0 | 0 |
| price.per_unit_currency | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| total_price.currency | 100 | 0 | 0 |
| total_price.period | 100 | 0 | 0 |
| size.acreage | 100 | 0 | 0 |
| size.sqm | 100 | 0 | 0 |
| size.hectares | 100 | 0 | 0 |
| floor | 100 | 0 | 0 |
| floors_total | 100 | 0 | 0 |
| condition | 100 | 0 | 0 |
| location.city | 100 | 0 | 0 |
| location.state | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | [""] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | ["string"] | [] |
| location.country | gs01_33 Unit Multifamily Development.pdf | USA | null |
| location.country | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | USA | null |
| location.zip | gs01_33 Unit Multifamily Development.pdf | null | 80231 |
| name | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 708-712 New Depot Street, Los Angeles, CA 90012 |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Ghobadi Multifamily Investment Team |
| size.sf | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 9506 | 27757.0 |
| size.units | gs01_33 Unit Multifamily Development.pdf | null | 33.0 |
| size.units | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 33.0 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000.0 |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
| type | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | residential | multifamily |
