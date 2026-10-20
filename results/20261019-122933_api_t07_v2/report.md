# Run 20261019-122933_api_t07_v2

| model | input | prompt | temp | top_p | docs |
|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | text | v2 | 0.7 | 0.9 | 2 |

## Metrics

- Field accuracy: 71.4%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 8.4s / 11.3s
- Cost per 1000 docs: $6.36

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| type_other | 0 | 0 | 1 |
| size.units | 0 | 0 | 2 |
| name | 50 | 1 | 0 |
| type | 50 | 0 | 0 |
| price.per_sf | 50 | 0 | 1 |
| price.per_sf_currency | 50 | 0 | 1 |
| price.per_unit | 50 | 0 | 1 |
| price.per_unit_currency | 50 | 0 | 1 |
| total_price.amount | 50 | 0 | 0 |
| size.sf | 50 | 0 | 0 |
| amenities | 50 | 1 | 0 |
| condition | 50 | 1 | 0 |
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
| location.city | 100 | 0 | 0 |
| location.state | 100 | 0 | 0 |
| location.country | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Most frequent errors

- `type_other` (2x): gs01_33 Unit Multifamily Development.pdf expected `Fully Entitled Development Land`, got `Multifamily Development`
- `size.units` (2x): gs01_33 Unit Multifamily Development.pdf expected `None`, got `33`
- `name` (1x): gs01_33 Unit Multifamily Development.pdf expected `33 Unit Multifamily Development`, got `None`
- `total_price.amount` (1x): gs01_33 Unit Multifamily Development.pdf expected `5531760`, got `1250000`
- `condition` (1x): gs01_33 Unit Multifamily Development.pdf expected `new_build`, got `None`
