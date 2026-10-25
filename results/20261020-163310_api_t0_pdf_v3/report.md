# Run 20261020-163310_api_t0_pdf_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | pdf | v3 | v2 | 0.0 | 1.0 | 2 |

## Metrics

- Field accuracy: 89.3%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 18.0s / 18.5s
- Cost per 1000 docs: $7.46

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| amenities | 0 | 0 | 2 |
| type | 50 | 0 | 0 |
| total_price.amount | 50 | 0 | 0 |
| location.country | 50 | 0 | 0 |
| seller | 50 | 0 | 0 |
| name | 100 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| type_other | 100 | 0 | 0 |
| price.per_sf | 100 | 0 | 0 |
| price.per_sf_currency | 100 | 0 | 0 |
| price.per_unit | 100 | 0 | 0 |
| price.per_unit_currency | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
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
| location.zip | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | [] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | [] | ["Parking: 36 Spaces", "Two Level Type I-A Subterranean Parking"] |
| location.country | gs01_33 Unit Multifamily Development.pdf | USA | US |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000 |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
