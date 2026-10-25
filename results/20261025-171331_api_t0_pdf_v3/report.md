# Run 20261025-171331_api_t0_pdf_v3

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| openrouter/openai/gpt-5.6-sol | pdf | v3 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 78.9%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 10.6s / 14.9s
- Cost per 1000 docs: $187.15

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| amenities | 0 | 0 | 3 |
| location.country | 0 | 0 | 0 |
| type_other | 10 | 0 | 9 |
| seller | 50 | 0 | 0 |
| floors_total | 60 | 0 | 3 |
| total_price.period | 70 | 2 | 1 |
| size.sf | 70 | 0 | 0 |
| condition | 70 | 0 | 1 |
| total_price.amount | 80 | 1 | 0 |
| location.state | 80 | 0 | 0 |
| location.street1 | 80 | 0 | 0 |
| name | 90 | 0 | 0 |
| price.per_sf | 90 | 0 | 1 |
| price.per_sf_currency | 90 | 1 | 0 |
| price.per_unit | 90 | 1 | 0 |
| price.per_unit_currency | 90 | 1 | 0 |
| total_price.currency | 90 | 1 | 0 |
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
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | ["Fully entitled and ready to develop", "Washer/dryer hookups in all proposed units", "Patio or balcony in all proposed units", "9-10 foot ceilings", "Covered parking for some units", "Elevator"] |
| amenities | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | [] | ["36 parking spaces", "Two-level Type I-A subterranean parking"] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["32 parking stalls plus 2 handicap spaces", "Controlled-access private underground parking", "Two levels of underground parking", "Elevator", "High-speed internet access", "Closed-circuit security system", "In-unit washers and dryers", "Central A/C and heat", "Fitness center", "Kitchen islands", "Key fob entry", "Video patrol", "EV chargers in parking spaces", "Designer granite countertops", "Balconies with views of Downtown Los Angeles, the San Gabriel Mountains and Dodger Stadium", "Rooftop lounge area with views of Downtown Los Angeles and Dodger Stadium", "Leasing office", "Separately metered utilities, including water"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["string"] | ["13 parking spaces, majority tandem", "Laundry facilities", "Separately metered electricity and gas", "Flat roof"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["18+ parking spaces", "HVAC/AC", "Quartz countertops", "Vinyl flooring", "New cabinetry", "Fencing", "Landscaping", "Septic sewer"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces"] | ["Interior courtyard", "Large multi-level atrium", "Rooftop amenities", "311 underground parking spaces", "Bicycle room with 102 bicycle parking spaces", "Pool", "Green roof"] |
| amenities | gs10_document.pdf | ["Climate-conscious service zones", "Reinforced terrace", "Gallery-grade art storage", "Glulam beams & shear walls"] | ["17,355 SF interior", "Private outdoor program", "Museum-scale gallery volume", "Engineered steel superstructure with aluminum and wood framing", "Glulam beams and shear walls", "Approximately 12+ engineered threaded-rod hanging points rated for up to 5,000 lb each", "Gallery-grade art storage", "Temperature-regulated garage, storage, shipping and receiving areas", "Reinforced terrace with double-door crane placement", "Garden", "Reflection pool"] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | [] | ["Large fenced and paved yard", "8 dock-high loading doors", "Fire sprinkler system", "600 amp, 277/480 volt, 3-phase, 4-wire power", "18-foot clear height", "2,000 SF office space", "Office heating and air conditioning", "2 restrooms", "56 parking spaces", "Easy access to the 5 and 91 freeways; 605 and 57 freeways nearby", "Tilt-up construction"] |
| amenities | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | [] | ["Utilities at the property", "3,273 feet of frontage along southbound I-45", "2,416 feet of frontage along FM-2004", "I-45 entrance in front of the property"] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["±14,976 SF contractor's yard", "±2,702 SF office/shop freestanding building", "Excellent street-to-alley access", "Huge secured concrete yard", "Kitchenette", "Convenient access to the 91 and 710 freeways", "Fenced yard", "12' clear height", "2 ground-level doors", "1 restroom", "4 parking spaces"] |
| condition | gs01_33 Unit Multifamily Development.pdf | new_build | unknown |
| condition | gs06_8000 Wisconsin Avenue.pdf | new_build | unknown |
| condition | gs10_document.pdf | null | unknown |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs04_5623+Meridian+Los+Angeles.pdf | null | 2 |
| floors_total | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | 1 |
| floors_total | gs06_8000 Wisconsin Avenue.pdf | null | 20 |
| location.country | gs01_33 Unit Multifamily Development.pdf | USA | United States |
| location.country | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | USA | United States |
| location.country | gs03_849+N+Bunker+Hill+OM.pdf | USA | United States |
| location.country | gs04_5623+Meridian+Los+Angeles.pdf | USA | United States |
| location.country | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | USA | United States |
| location.country | gs06_8000 Wisconsin Avenue.pdf | USA | United States |
| location.country | gs10_document.pdf | USA | United States |
| location.country | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | USA | United States |
| location.country | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | USA | United States |
| location.country | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | USA | United States |
| location.state | gs01_33 Unit Multifamily Development.pdf | CO | Colorado |
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
| seller | gs10_document.pdf | TheAgencyRE | The Agency — Mauricio Umansky and Lorán Arvizu |
| size.sf | gs03_849+N+Bunker+Hill+OM.pdf | 12197 | 30660 |
| size.sf | gs04_5623+Meridian+Los+Angeles.pdf | 12615 | 11738 |
| size.sf | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | 7510 | 2702 |
| total_price.amount | gs01_33 Unit Multifamily Development.pdf | 5531760 | 1250000 |
| total_price.amount | gs03_849+N+Bunker+Hill+OM.pdf | 1699500 | null |
| total_price.currency | gs03_849+N+Bunker+Hill+OM.pdf | USD | null |
| total_price.period | gs03_849+N+Bunker+Hill+OM.pdf | one_time | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| total_price.period | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | one_time |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Multifamily - Under Construction |
| type_other | gs03_849+N+Bunker+Hill+OM.pdf | null | Multifamily apartment building |
| type_other | gs04_5623+Meridian+Los+Angeles.pdf | null | Multifamily |
| type_other | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | Single Story Garden Style multifamily |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | Mixed Use Multifamily Development Opportunity |
| type_other | gs10_document.pdf | null | Art gallery / architectural commercial asset |
| type_other | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | Free Standing Warehouse/Distribution Building |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | Land |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | Warehouse/Office |
