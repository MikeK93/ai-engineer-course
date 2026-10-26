# Run 20261026-121226_local_t0_text_v4

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| ollama_chat/qwen2.5:3b | text | v4 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 49.3%
- Valid responses: 90.0% (first try 90.0%, failed 1)
- Latency p50 / p95: 57.8s / 88.4s
- Cost per 1000 docs: $0.00

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| amenities | 0 | 1 | 0 |
| location.country | 0 | 0 | 0 |
| name | 10 | 0 | 5 |
| total_price.period | 10 | 7 | 0 |
| floors_total | 10 | 4 | 3 |
| seller | 10 | 6 | 0 |
| type_other | 30 | 0 | 5 |
| size.sf | 30 | 5 | 0 |
| condition | 30 | 2 | 1 |
| price.per_sf | 40 | 5 | 0 |
| price.per_sf_currency | 40 | 5 | 0 |
| total_price.amount | 40 | 4 | 0 |
| floor | 40 | 0 | 5 |
| type | 50 | 0 | 0 |
| total_price.label | 50 | 1 | 3 |
| total_price.currency | 50 | 4 | 0 |
| size.units | 50 | 3 | 0 |
| price.per_unit | 70 | 1 | 0 |
| size.acreage | 70 | 2 | 0 |
| deal_type | 80 | 0 | 0 |
| price.per_unit_currency | 80 | 1 | 0 |
| size.sqm | 80 | 0 | 1 |
| size.hectares | 80 | 0 | 1 |
| location.state | 80 | 0 | 0 |
| location.street1 | 80 | 0 | 0 |
| location.city | 90 | 0 | 0 |
| location.zip | 90 | 0 | 0 |
| location.street2 | 90 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["elevator", "covered parking"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | ["36 parking spaces", "Two-level Type I-A subterranean parking"] | ["36 Spaces, Two Level Type I-A Subterranean Parking", "33 Apartment Units", "6-Story Building", "Very Low Income Units (3 Units)"] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["Controlled Access with Private Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel Mountains and Dodger Stadium", "Leasing Office", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["13 parking spaces, majority tandem", "Laundry facilities", "Separately metered electricity and gas", "Flat roof"] | ["Majority Tandem Parking", "Soft Story", "Separately Metered Electricity and Gas"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["18+ parking spaces", "HVAC/AC", "Quartz countertops", "Vinyl flooring", "New cabinetry", "Fencing", "Landscaping", "Septic sewer", "Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["new plumbing supply", "electrical", "roofs", "AC", "windows", "stucco", "paint", "full gut"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces", "Interior courtyard", "Large multi-level atrium", "Rooftop amenities", "Pool", "Green roof"] | ["large multi-level atrium", "interior courtyard", "roof top amenities", "abundant on-site parking"] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | ["Large fenced and paved yard", "8 dock-high loading doors", "Fire sprinkler system", "600 amp, 277/480 volt, 3-phase, 4-wire power", "18-foot clear height", "2,000 SF office space", "Office heating and air conditioning", "2 restrooms", "56 parking spaces", "Easy access to the 5 and 91 freeways; 605 and 57 freeways nearby", "Tilt-up construction"] | ["8 Dock High Loading", "Large Fenced Yard", "Calculated Fire Sprk System", "600 Amp, 277/480 Volt Power", "Easy Access to 5 & 91 Fwys + 605 & 57 Close", "Industrial For Lease", "Parking includes potential spaces in fenced yard area", "Fenced / Paved", "MH", "GL Doors/Dim: TILT UP", "Office HVAC: No", "Whse HVAC: No", "Rail Service: Manufacturing", "Specific Use: 2.0:1 / Ratio: A: 600 V: 277/480 0: 3 W: 4", "Construction Type: Existing / 1968", "Office SF / #: 2", "Restrooms: 2", "Heat & AC: Yes"] |
| amenities | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | ["Utilities at the property", "3,273 feet of frontage along southbound I-45", "2,416 feet of frontage along FM-2004", "I-45 entrance in front of the property"] | [] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["Kitchenette", "Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Convenient Access to the 91 and 710 Freeways", "Industrial For Lease", "Fenced"] |
| condition | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | under_construction | null |
| condition | gs04_5623+Meridian+Los+Angeles.pdf | needs_renovation | new_build |
| condition | gs06_8000 Wisconsin Avenue.pdf | under_construction | new_build |
| condition | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | unknown | new_build |
| condition | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | new_build |
| condition | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | unknown | null |
| deal_type | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | lease | sale |
| floor | gs01_33 Unit Multifamily Development.pdf | null | 9 |
| floor | gs03_849+N+Bunker+Hill+OM.pdf | null | 6 |
| floor | gs04_5623+Meridian+Los+Angeles.pdf | null | 2 |
| floor | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | 1 |
| floor | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | 0 |
| floors_total | gs01_33 Unit Multifamily Development.pdf | null | 1 |
| floors_total | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 6 | null |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs04_5623+Meridian+Los+Angeles.pdf | 2 | null |
| floors_total | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 1 | null |
| floors_total | gs06_8000 Wisconsin Avenue.pdf | 20 | null |
| floors_total | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | 0 |
| floors_total | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | 2918520 |
| location.country | gs01_33 Unit Multifamily Development.pdf | US | USA |
| location.country | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | US | USA |
| location.country | gs03_849+N+Bunker+Hill+OM.pdf | US | USA |
| location.country | gs04_5623+Meridian+Los+Angeles.pdf | US | USA |
| location.country | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | US | USA |
| location.country | gs06_8000 Wisconsin Avenue.pdf | US | USA |
| location.country | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | US | USA |
| location.country | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | US | USA |
| location.country | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | US | USA |
| location.state | gs06_8000 Wisconsin Avenue.pdf | MD | Maryland |
| location.street1 | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 6535 OASIS AVENUE | 6563 Oasis Avenue |
| name | gs01_33 Unit Multifamily Development.pdf | 33 Unit Multifamily Development | 9850 East Girard Avenue |
| name | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | 708-712 New Depot Street |
| name | gs03_849+N+Bunker+Hill+OM.pdf | Bunker Height's Apartment Homes | Multifamily |
| name | gs04_5623+Meridian+Los+Angeles.pdf | null | Multifamily |
| name | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | 6563 Oasis Avenue |
| name | gs06_8000 Wisconsin Avenue.pdf | 8000 Wisconsin | 8000 Wisconsin Avenue |
| name | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | 6310 Caballero Blvd |
| name | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | 16213 Illinois Ave |
| price.per_sf | gs03_849+N+Bunker+Hill+OM.pdf | 554.31 | null |
| price.per_sf | gs04_5623+Meridian+Los+Angeles.pdf | 357.81 | null |
| price.per_sf | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 324.68 | null |
| price.per_sf | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | 1.49 | null |
| price.per_sf | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 2.94 | null |
| price.per_sf_currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| price.per_sf_currency | gs04_5623+Meridian+Los+Angeles.pdf | USD | null |
| price.per_sf_currency | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USD | null |
| price.per_sf_currency | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | USD | null |
| price.per_sf_currency | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | USD | null |
| price.per_unit | gs01_33 Unit Multifamily Development.pdf | 37879 | 167629 |
| price.per_unit | gs03_849+N+Bunker+Hill+OM.pdf | 459324 | null |
| price.per_unit_currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| seller | gs01_33 Unit Multifamily Development.pdf | Marcus & Millichap | Marcus & Millichap Real Estate Investment Services, Inc. |
| seller | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | Colliers | null |
| seller | gs03_849+N+Bunker+Hill+OM.pdf | Colliers | null |
| seller | gs04_5623+Meridian+Los+Angeles.pdf | Colliers | null |
| seller | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | Commercial Asset Advisors | null |
| seller | gs06_8000 Wisconsin Avenue.pdf | Newmark | null |
| seller | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | Texas Commercial Properties | Texas Commercial Properties, 3121 Oak Drive, Dickinson, TX 77539, 281-650-4875, WHITELAUREN@COMCAST.NET |
| seller | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | Daum Commercial | null |
| size.acreage | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | 67.16 | null |
| size.acreage | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 0.17 | null |
| size.hectares | gs01_33 Unit Multifamily Development.pdf | null | 0.078 |
| size.sf | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 9506 | null |
| size.sf | gs03_849+N+Bunker+Hill+OM.pdf | 12197 | null |
| size.sf | gs04_5623+Meridian+Los+Angeles.pdf | 12615 | 11738 |
| size.sf | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | 28000 | null |
| size.sf | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | 2918520 | null |
| size.sf | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 7510 | null |
| size.sqm | gs01_33 Unit Multifamily Development.pdf | null | 7800 |
| size.units | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 33 | null |
| size.units | gs03_849+N+Bunker+Hill+OM.pdf | 37 | null |
| size.units | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 9 | null |
| size.units | gs06_8000 Wisconsin Avenue.pdf | 437 | 0.94 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 1250000 | 5531760 |
| total_price.amount | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | 6450000 | null |
| total_price.amount | gs03_849+N+Bunker+Hill+OM.pdf | 16995000 | null |
| total_price.amount | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | 41720 | null |
| total_price.amount | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 7937 | null |
| total_price.currency | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | USD | null |
| total_price.currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| total_price.currency | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | USD | null |
| total_price.currency | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | USD | null |
| total_price.label | gs01_33 Unit Multifamily Development.pdf | null | Estimated Project Cost (Inc. Land) |
| total_price.label | gs04_5623+Meridian+Los+Angeles.pdf | null | List Price |
| total_price.label | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | Price |
| total_price.label | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | Negotiable | null |
| total_price.period | gs01_33 Unit Multifamily Development.pdf | one_time | yearly |
| total_price.period | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | one_time | null |
| total_price.period | gs03_849+N+Bunker+Hill+OM.pdf | one_time | null |
| total_price.period | gs04_5623+Meridian+Los+Angeles.pdf | one_time | null |
| total_price.period | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | one_time | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| total_price.period | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | monthly | null |
| total_price.period | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | monthly | null |
| type | gs01_33 Unit Multifamily Development.pdf | land | multifamily |
| type | gs06_8000 Wisconsin Avenue.pdf | multifamily/mixed_use | mixed_use |
| type | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | industrial | warehouse |
| type | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | Warehouse/Office | office |
| type_other | gs01_33 Unit Multifamily Development.pdf | Fully Entitled Development Land | development |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | under construction |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | multifamily |
| type_other | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | distribution |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | commercial |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | shop |
