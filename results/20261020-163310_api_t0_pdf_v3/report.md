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

## Most frequent errors

- `amenities` (2x): gs01_33 Unit Multifamily Development.pdf expected `[]`, got `['washer/dryer hookups', 'patio/balcony', '9-10 foot ceilings', 'covered parking', 'fully enclosed building', 'elevator']`
- `type` (1x): gs01_33 Unit Multifamily Development.pdf expected `land`, got `multifamily`
- `total_price.amount` (1x): gs01_33 Unit Multifamily Development.pdf expected `5531760`, got `1250000`
- `location.country` (1x): gs01_33 Unit Multifamily Development.pdf expected `USA`, got `US`
- `seller` (1x): gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf expected `Ghobadi Multifamily Investment Team - Colliers`, got `Colliers`
