# Run 20261025-170855_api_t0_pdf_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| openrouter/google/gemini-2.5-flash | pdf | v3 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 83.2%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 5.4s / 9.0s
- Cost per 1000 docs: $1.67

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| amenities | 10 | 1 | 2 |
| seller | 40 | 0 | 0 |
| type_other | 60 | 0 | 3 |
| size.sf | 60 | 0 | 0 |
| floors_total | 60 | 0 | 3 |
| condition | 60 | 0 | 2 |
| type | 80 | 0 | 0 |
| total_price.amount | 80 | 1 | 0 |
| total_price.period | 80 | 2 | 0 |
| location.street1 | 80 | 0 | 0 |
| name | 90 | 1 | 0 |
| deal_type | 90 | 1 | 0 |
| price.per_sf | 90 | 0 | 1 |
| price.per_sf_currency | 90 | 1 | 0 |
| price.per_unit | 90 | 1 | 0 |
| price.per_unit_currency | 90 | 1 | 0 |
| total_price.currency | 90 | 1 | 0 |
| location.state | 90 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| size.units | 100 | 0 | 0 |
| size.acreage | 100 | 0 | 0 |
| size.sqm | 100 | 0 | 0 |
| size.hectares | 100 | 0 | 0 |
| floor | 100 | 0 | 0 |
| location.city | 100 | 0 | 0 |
| location.country | 100 | 0 | 0 |
| location.zip | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | [] | ["Parking: 36 Spaces", "Two Level Type I-A Subterranean"] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office", "Separately Metered for All Utilities, Including Water"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["string"] | ["Parking", "Separately metered electricity and gas"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["New Plumbing", "Electrical", "Roofs", "AC", "Windows", "Stucco", "Paint", "Full Gut Interior Rehab", "Parking: 18+ Spaces", "Single Water, Gas & Electricity Metering", "Septic Sewer"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces"] | ["interior courtyard", "multi-level atrium", "rooftop amenities", "on-site parking", "underground parking", "bicycle room", "pool", "green roof"] |
| amenities | gs10_document.pdf | ["Climate-conscious service zones", "Reinforced terrace", "Gallery-grade art storage", "Glulam beams & shear walls"] | [] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | [] | ["Fenced Yard", "Heat & AC", "Sprinklered"] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["Kitchenette", "Sprinklered", "Fenced", "Secured Concrete Yard"] |
| condition | gs04_5623+Meridian+Los+Angeles.pdf | needs_renovation | unknown |
| condition | gs06_8000 Wisconsin Avenue.pdf | new_build | under_construction |
| condition | gs10_document.pdf | null | unknown |
| condition | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | unknown |
| deal_type | gs03_849+N+Bunker+Hill+OM.pdf | sale | null |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs04_5623+Meridian+Los+Angeles.pdf | null | 2 |
| floors_total | gs06_8000 Wisconsin Avenue.pdf | null | 20 |
| floors_total | gs10_document.pdf | null | 3 |
| location.state | gs06_8000 Wisconsin Avenue.pdf | MD | Maryland |
| location.street1 | gs04_5623+Meridian+Los+Angeles.pdf | 5623 Meridian Avenue | 5623 Meridian Street |
| location.street1 | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 6535 OASIS AVENUE | 6563 Oasis Avenue |
| name | gs03_849+N+Bunker+Hill+OM.pdf | Bunker Height's Apartment Homes | null |
| price.per_sf | gs04_5623+Meridian+Los+Angeles.pdf | null | 357.81 |
| price.per_sf_currency | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USD | null |
| price.per_unit | gs03_849+N+Bunker+Hill+OM.pdf | 459324 | null |
| price.per_unit_currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| seller | gs03_849+N+Bunker+Hill+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Ghobadi Multifamily Investment Team |
| seller | gs04_5623+Meridian+Los+Angeles.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| seller | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | Commertial Asset Advisors | COMMERCIAL ASSET ADVISORS |
| seller | gs10_document.pdf | TheAgencyRE | Mauricio Umansky \| Lorán Arvizu |
| seller | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | Texas Commercial Properties | Lauren J White |
| size.sf | gs03_849+N+Bunker+Hill+OM.pdf | 12197 | 30660 |
| size.sf | gs04_5623+Meridian+Los+Angeles.pdf | 12615 | 11738 |
| size.sf | gs10_document.pdf | 37312 | 17355 |
| size.sf | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 7510 | 2702 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000 |
| total_price.amount | gs03_849+N+Bunker+Hill+OM.pdf | 1699500 | null |
| total_price.currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| total_price.period | gs03_849+N+Bunker+Hill+OM.pdf | one_time | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
| type | gs06_8000 Wisconsin Avenue.pdf | multifamily/mixed_use | mixed_use |
| type_other | gs01_33 Unit Multifamily Development.pdf | Fully Entitled Development Land | Multifamily - 33 Units |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | MIXED USE MULTIFAMILY DEVELOPMENT OPPORTUNITY |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | Land |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | Warehouse/Office |
