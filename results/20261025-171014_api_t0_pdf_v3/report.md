# Run 20261025-171014_api_t0_pdf_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| openrouter/google/gemini-3.5-flash | pdf | v3 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 78.6%
- Valid responses: 100.0% (first try 90.0%, failed 0)
- Latency p50 / p95: 15.0s / 28.8s
- Cost per 1000 docs: $35.15

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| location.country | 0 | 0 | 0 |
| type_other | 10 | 0 | 9 |
| amenities | 10 | 0 | 2 |
| seller | 40 | 0 | 0 |
| condition | 50 | 0 | 2 |
| size.sf | 60 | 0 | 0 |
| floors_total | 60 | 0 | 3 |
| total_price.amount | 80 | 1 | 0 |
| total_price.period | 80 | 2 | 0 |
| location.street1 | 80 | 0 | 0 |
| name | 90 | 0 | 0 |
| price.per_sf | 90 | 0 | 1 |
| price.per_sf_currency | 90 | 1 | 0 |
| price.per_unit | 90 | 1 | 0 |
| price.per_unit_currency | 90 | 1 | 0 |
| total_price.currency | 90 | 1 | 0 |
| location.state | 90 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| type | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| size.units | 100 | 0 | 0 |
| size.acreage | 100 | 0 | 0 |
| size.sqm | 100 | 0 | 0 |
| size.hectares | 100 | 0 | 0 |
| floor | 100 | 0 | 0 |
| location.city | 100 | 0 | 0 |
| location.zip | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | [] | ["36 Parking Spaces", "Two Level Type I-A Subterranean Parking"] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies", "Rooftop Lounge Area", "Leasing Office", "Underground Parking"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["string"] | ["Parking"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["quartz countertops", "vinyl flooring", "new cabinetry", "fencing", "landscaping", "parking", "air conditioning"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces"] | ["interior courtyard", "large multi-level atrium", "rooftop amenities", "below grade garage", "underground parking", "bicycle room", "pool", "green roof"] |
| amenities | gs10_document.pdf | ["Climate-conscious service zones", "Reinforced terrace", "Gallery-grade art storage", "Glulam beams & shear walls"] | ["private outdoor program", "art storage", "reinforced terrace", "garage", "garden", "reflection pool"] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | [] | ["Fenced Yard", "Dock High Loading", "Fire Sprinkler System", "Office HVAC", "Restrooms", "Parking"] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["Contractor's Yard", "Office/Shop Freestanding Building", "Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Fenced Yard"] |
| condition | gs01_33 Unit Multifamily Development.pdf | new_build | unknown |
| condition | gs04_5623+Meridian+Los+Angeles.pdf | needs_renovation | unknown |
| condition | gs06_8000 Wisconsin Avenue.pdf | new_build | under_construction |
| condition | gs10_document.pdf | null | unknown |
| condition | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | unknown |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs04_5623+Meridian+Los+Angeles.pdf | null | 2 |
| floors_total | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | 1 |
| floors_total | gs06_8000 Wisconsin Avenue.pdf | null | 20 |
| location.country | gs01_33 Unit Multifamily Development.pdf | USA | US |
| location.country | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | USA | US |
| location.country | gs03_849+N+Bunker+Hill+OM.pdf | USA | US |
| location.country | gs04_5623+Meridian+Los+Angeles.pdf | USA | US |
| location.country | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USA | US |
| location.country | gs06_8000 Wisconsin Avenue.pdf | USA | United States |
| location.country | gs10_document.pdf | USA | US |
| location.country | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | USA | US |
| location.country | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | USA | US |
| location.country | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | USA | US |
| location.state | gs06_8000 Wisconsin Avenue.pdf | MD | Maryland |
| location.street1 | gs04_5623+Meridian+Los+Angeles.pdf | 5623 Meridian Avenue | 5623 Meridian Street |
| location.street1 | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 6535 OASIS AVENUE | 6563 Oasis Avenue |
| name | gs03_849+N+Bunker+Hill+OM.pdf | Bunker Height's Apartment Homes | Bunker Height’s Apartment Homes |
| price.per_sf | gs04_5623+Meridian+Los+Angeles.pdf | null | 357.81 |
| price.per_sf_currency | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USD | null |
| price.per_unit | gs03_849+N+Bunker+Hill+OM.pdf | 459324 | null |
| price.per_unit_currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| seller | gs03_849+N+Bunker+Hill+OM.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| seller | gs04_5623+Meridian+Los+Angeles.pdf | Ghobadi Multifamily Investment Team - Colliers | Colliers |
| seller | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | Commertial Asset Advisors | Commercial Asset Advisors |
| seller | gs10_document.pdf | TheAgencyRE | The Agency |
| seller | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | Texas Commercial Properties | Lauren J White, Texas Commercial Properties |
| size.sf | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 9506 | 27757 |
| size.sf | gs03_849+N+Bunker+Hill+OM.pdf | 12197 | 30660 |
| size.sf | gs10_document.pdf | 37312 | 17355 |
| size.sf | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 7510 | 2702 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000 |
| total_price.amount | gs03_849+N+Bunker+Hill+OM.pdf | 1699500 | null |
| total_price.currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| total_price.period | gs03_849+N+Bunker+Hill+OM.pdf | one_time | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Multifamily - Under Construction |
| type_other | gs03_849+N+Bunker+Hill+OM.pdf | null | Apartment Building |
| type_other | gs04_5623+Meridian+Los+Angeles.pdf | null | Multifamily |
| type_other | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | multifamily |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | Mixed Use Multifamily Development Opportunity |
| type_other | gs10_document.pdf | null | Gallery |
| type_other | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | Free Standing Warehouse/Distribution Building |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | Land |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | Warehouse/Office |
