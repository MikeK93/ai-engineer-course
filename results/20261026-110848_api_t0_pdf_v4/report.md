# Run 20261026-110848_api_t0_pdf_v4

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| openrouter/google/gemini-3.5-flash | pdf | v4 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 86.1%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 14.9s / 19.4s
- Cost per 1000 docs: $33.72

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| amenities | 0 | 1 | 0 |
| type_other | 10 | 0 | 9 |
| name | 70 | 2 | 0 |
| floors_total | 70 | 1 | 1 |
| total_price.amount | 80 | 1 | 0 |
| total_price.period | 80 | 2 | 0 |
| condition | 80 | 0 | 1 |
| type | 90 | 0 | 0 |
| price.per_sf_currency | 90 | 1 | 0 |
| price.per_unit | 90 | 1 | 0 |
| price.per_unit_currency | 90 | 1 | 0 |
| total_price.currency | 90 | 1 | 0 |
| size.sf | 90 | 0 | 0 |
| location.street1 | 90 | 0 | 0 |
| seller | 90 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| price.per_sf | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| size.units | 100 | 0 | 0 |
| size.acreage | 100 | 0 | 0 |
| size.sqm | 100 | 0 | 0 |
| size.hectares | 100 | 0 | 0 |
| floor | 100 | 0 | 0 |
| location.city | 100 | 0 | 0 |
| location.state | 100 | 0 | 0 |
| location.country | 100 | 0 | 0 |
| location.zip | 100 | 0 | 0 |
| location.street2 | 100 | 0 | 0 |

## Errors

| Field | File | Expected | Got |
|---|---|---|---|
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | ["36 parking spaces", "Two-level Type I-A subterranean parking"] | ["Parking"] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["Controlled Access", "Private Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers", "Designer Granite Countertops", "Balconies", "Rooftop Lounge Area", "Leasing Office"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["13 parking spaces, majority tandem", "Laundry facilities", "Separately metered electricity and gas", "Flat roof"] | ["Parking"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["18+ parking spaces", "HVAC/AC", "Quartz countertops", "Vinyl flooring", "New cabinetry", "Fencing", "Landscaping", "Septic sewer", "Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["HVAC", "Quartz Countertops", "Vinyl Flooring", "New Cabinetry", "Fencing", "Landscaping", "18+ Parking Spaces"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces", "Interior courtyard", "Large multi-level atrium", "Rooftop amenities", "Pool", "Green roof"] | ["interior courtyard", "multi-level atrium", "rooftop amenities", "underground parking", "bicycle room", "pool"] |
| amenities | gs10_document.pdf | ["Climate-conscious service zones", "Private outdoor program", "Museum-scale gallery volume", "Engineered steel superstructure with aluminum and wood framing", "Glulam beams and shear walls", "Approximately 12+ engineered threaded-rod hanging points rated for up to 5,000 lb each", "Gallery-grade art storage", "Temperature-regulated garage, storage, shipping and receiving areas", "Reinforced terrace with double-door crane placement", "Garden", "Reflection pool"] | ["Private outdoor program", "Engineered hanging points", "Gallery-grade art storage", "Climate-conscious service zones", "Reinforced terrace", "Garage"] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | ["Large fenced and paved yard", "8 dock-high loading doors", "Fire sprinkler system", "600 amp, 277/480 volt, 3-phase, 4-wire power", "18-foot clear height", "2,000 SF office space", "Office heating and air conditioning", "2 restrooms", "56 parking spaces", "Easy access to the 5 and 91 freeways; 605 and 57 freeways nearby", "Tilt-up construction"] | ["Fenced Yard", "Paved Yard", "Fire Sprinkler System", "Dock High Loading", "Office HVAC"] |
| amenities | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | ["Utilities at the property", "3,273 feet of frontage along southbound I-45", "2,416 feet of frontage along FM-2004", "I-45 entrance in front of the property"] | [] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["Contractor's Yard", "Secured Concrete Yard", "Kitchenette", "Fenced Yard"] |
| condition | gs04_5623+Meridian+Los+Angeles.pdf | needs_renovation | unknown |
| condition | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | unknown |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs10_document.pdf | 3 | null |
| floors_total | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | 1 |
| location.street1 | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 6535 OASIS AVENUE | 6563 Oasis Avenue |
| name | gs01_33 Unit Multifamily Development.pdf | 33 Unit Multifamily Development | null |
| name | gs03_849+N+Bunker+Hill+OM.pdf | Bunker Height's Apartment Homes | Bunker Height’s Apartment Homes |
| name | gs06_8000 Wisconsin Avenue.pdf | 8000 Wisconsin | null |
| price.per_sf_currency | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USD | null |
| price.per_unit | gs03_849+N+Bunker+Hill+OM.pdf | 459324 | null |
| price.per_unit_currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| seller | gs10_document.pdf | TheAgencyRE | The Agency |
| size.sf | gs10_document.pdf | 37312 | 17355 |
| total_price.amount | gs03_849+N+Bunker+Hill+OM.pdf | 1699500 | null |
| total_price.amount | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 2702 | 7937 |
| total_price.currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| total_price.period | gs03_849+N+Bunker+Hill+OM.pdf | one_time | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| type | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | Warehouse/Office | industrial |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Multifamily - Under Construction |
| type_other | gs03_849+N+Bunker+Hill+OM.pdf | null | Apartment Building |
| type_other | gs04_5623+Meridian+Los+Angeles.pdf | null | Multifamily |
| type_other | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | Multifamily |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | Mixed Use Multifamily Development Opportunity |
| type_other | gs10_document.pdf | null | Gallery |
| type_other | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | Warehouse/Distribution Building |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | Land |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | Industrial |
