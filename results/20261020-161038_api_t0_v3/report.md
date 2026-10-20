# Run 20261020-161038_api_t0_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| gemini/gemini-2.5-flash | text | v3 | v2 | 0.0 | 1.0 | 2 |

## Metrics

- Field accuracy: 91.1%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 8.6s / 11.6s
- Cost per 1000 docs: $6.07

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| name | 50 | 1 | 0 |
| type_other | 50 | 0 | 1 |
| total_price.amount | 50 | 0 | 0 |
| amenities | 50 | 0 | 1 |
| seller | 50 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| type | 100 | 0 | 0 |
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
| location.country | 100 | 0 | 0 |
| location.zip | 100 | 0 | 0 |
| location.street1 | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Most frequent errors

- `name` (1x): gs01_33 Unit Multifamily Development.pdf expected `33 Unit Multifamily Development`, got `None`
- `total_price.amount` (1x): gs01_33 Unit Multifamily Development.pdf expected `5531760`, got `1250000`
- `type_other` (1x): gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf expected `None`, got `Multifamily`
- `amenities` (1x): gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf expected `[]`, got `['Parking: 36 Spaces, Two Level Type I-A Subterranean']`
- `seller` (1x): gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf expected `Ghobadi Multifamily Investment Team - Colliers`, got `Colliers`
