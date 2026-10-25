# Run 20261018-143618_api_t0_v2

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | text | v2 | v1 | 0.0 | 1.0 | 2 |

## Metrics

- Field accuracy: 71.4%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 8.7s / 14.5s
- Cost per 1000 docs: $7.61

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| type | 0 | 0 | 0 |
| size.units | 0 | 0 | 2 |
| amenities | 0 | 1 | 1 |
| name | 50 | 1 | 0 |
| type_other | 50 | 0 | 1 |
| price.per_sf | 50 | 0 | 1 |
| price.per_sf_currency | 50 | 0 | 1 |
| price.per_unit | 50 | 0 | 1 |
| price.per_unit_currency | 50 | 0 | 1 |
| total_price.amount | 50 | 0 | 0 |
| size.sf | 50 | 0 | 0 |
| location.zip | 50 | 0 | 1 |
| seller | 50 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
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
| location.country | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | [""] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | ["string"] | [] |
| location.zip | gs01_33 Unit Multifamily Development.pdf | null | 80231 |
| name | gs01_33 Unit Multifamily Development.pdf | 33 Unit Multifamily Development | null |
| price.per_sf | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 279.34 |
| price.per_sf_currency | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | USD |
| price.per_unit | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 195454.55 |
| price.per_unit_currency | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | USD |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| size.sf | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 9506 | 23090.0 |
| size.units | gs01_33 Unit Multifamily Development.pdf | null | 33.0 |
| size.units | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 33.0 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000.0 |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
| type | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | residential | multifamily |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Apartment Units |
