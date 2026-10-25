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

## Most frequent errors

- `type_other` (2x): gs01_33 Unit Multifamily Development.pdf expected `Fully Entitled Development Land`, got `Multifamily Development`
- `amenities` (2x): gs01_33 Unit Multifamily Development.pdf expected `['washer/dryer hookups', 'patio/balcony', '9-10 foot ceilings', 'covered parking', 'fully enclosed building', 'elevator']`, got `['washer/dryer hookups', 'patio/balcony', '9-10 foot ceilings', 'covered parking', 'elevator']`
- `name` (1x): gs01_33 Unit Multifamily Development.pdf expected `33 Unit Multifamily Development`, got `None`
- `type` (1x): gs01_33 Unit Multifamily Development.pdf expected `land`, got `multifamily`
- `price.per_sf` (1x): gs01_33 Unit Multifamily Development.pdf expected `36.68`, got `174.39`
