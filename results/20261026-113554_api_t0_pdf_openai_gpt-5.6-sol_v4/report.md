# Run 20261026-113554_api_t0_pdf_openai_gpt-5.6-sol_v4

| model | input | prompt | golden | temp | top_p | docs |
|---|---|---|---|---|---|---|
| openrouter/openai/gpt-5.6-sol | pdf | v4 | latest | 0.0 | 1.0 | 10 |

## Metrics

- Field accuracy: 85.4%
- Valid responses: 100.0% (first try 100.0%, failed 0)
- Latency p50 / p95: 11.1s / 42.0s
- Cost per 1000 docs: $248.27

## Per-field accuracy

| field | accuracy % | missed (null) | hallucinated |
|---|---|---|---|
| type_other | 10 | 0 | 9 |
| amenities | 10 | 1 | 0 |
| location.state | 20 | 0 | 0 |
| type | 70 | 0 | 0 |
| condition | 70 | 0 | 1 |
| name | 80 | 1 | 0 |
| total_price.period | 80 | 1 | 1 |
| floors_total | 80 | 1 | 0 |
| size.units | 90 | 1 | 0 |
| location.street1 | 90 | 0 | 0 |
| seller | 90 | 0 | 0 |
| deal_type | 100 | 0 | 0 |
| price.per_sf | 100 | 0 | 0 |
| price.per_sf_currency | 100 | 0 | 0 |
| price.per_unit | 100 | 0 | 0 |
| price.per_unit_currency | 100 | 0 | 0 |
| total_price.label | 100 | 0 | 0 |
| total_price.amount | 100 | 0 | 0 |
| total_price.currency | 100 | 0 | 0 |
| size.sf | 100 | 0 | 0 |
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
| amenities | gs01_33 Unit Multifamily Development.pdf | ["washer/dryer hookups", "patio/balcony", "9-10 foot ceilings", "covered parking", "fully enclosed building", "elevator"] | [] |
| amenities | gs03_849+N+Bunker+Hill+OM.pdf | ["Controlled Access with Private Underground Parking. Two levels of Underground Parking", "Elevator", "High Speed Internet Access", "Closed-Circuit Security System", "In-Unit Washers & Dryers", "Central A/C and Heat", "Fitness Center", "Kitchen Island", "Key Fob Entry", "Video Patrol", "EV Chargers in Parking Spaces", "Designer Granite Countertops", "Balconies with Fantastic Views of Downtown Los Angeles, the San Gabriel", "Mountains and Dodger Stadium", "Walking Distance to Union Station", "Rooftop Lounge Area with View of L.A. Downtown and Dodger Stadium", "Leasing Office"] | ["32 parking stalls plus 2 handicap spaces", "Two levels of private underground parking", "Controlled access", "Elevator", "High-speed internet access", "Closed-circuit security system", "In-unit washers and dryers", "Central air conditioning and heat", "Fitness center", "Kitchen islands", "Key fob entry", "Video patrol", "EV chargers in parking spaces", "Designer granite countertops", "Balconies with views of Downtown Los Angeles, the San Gabriel Mountains, and Dodger Stadium", "Rooftop lounge area", "Leasing office", "Separately metered utilities, including water"] |
| amenities | gs04_5623+Meridian+Los+Angeles.pdf | ["13 parking spaces, majority tandem", "Laundry facilities", "Separately metered electricity and gas", "Flat roof"] | ["13 parking spaces, majority tandem", "Laundry facilities", "Separately metered electricity and gas"] |
| amenities | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | ["18+ parking spaces", "HVAC/AC", "Quartz countertops", "Vinyl flooring", "New cabinetry", "Fencing", "Landscaping", "Septic sewer", "Only a few miles from the famous Joshua Tree State Park", "Only blocks away from Freedom Plaza, the heart of Downtown Twentynine Palms", "New Plumbing, Electrical, Roofs, AC, Windows, Stucco", "Paint, & Full Gut Interior Rehab"] | ["18+ parking spaces", "Laundry", "Storage room", "Yards for studio units", "HVAC", "Quartz countertops", "Vinyl flooring", "New cabinetry", "Fencing", "Landscaping", "Septic sewer system"] |
| amenities | gs06_8000 Wisconsin Avenue.pdf | ["311 Parking Spaces Spaces", "Bicycle Room for 102 Bicycles", "Parking Spaces", "Interior courtyard", "Large multi-level atrium", "Rooftop amenities", "Pool", "Green roof"] | ["Interior courtyard", "Multi-level atrium", "Rooftop amenities", "Rooftop pool", "Green roof", "311 underground parking spaces", "Bicycle room with 102 bicycle parking spaces"] |
| amenities | gs10_document.pdf | ["Climate-conscious service zones", "Private outdoor program", "Museum-scale gallery volume", "Engineered steel superstructure with aluminum and wood framing", "Glulam beams and shear walls", "Approximately 12+ engineered threaded-rod hanging points rated for up to 5,000 lb each", "Gallery-grade art storage", "Temperature-regulated garage, storage, shipping and receiving areas", "Reinforced terrace with double-door crane placement", "Garden", "Reflection pool"] | ["Private outdoor program", "Long-span gallery space", "Engineered hanging points", "Gallery-grade art storage", "Temperature-regulated garage, storage, shipping and receiving areas", "Reinforced terrace"] |
| amenities | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | ["Large fenced and paved yard", "8 dock-high loading doors", "Fire sprinkler system", "600 amp, 277/480 volt, 3-phase, 4-wire power", "18-foot clear height", "2,000 SF office space", "Office heating and air conditioning", "2 restrooms", "56 parking spaces", "Easy access to the 5 and 91 freeways; 605 and 57 freeways nearby", "Tilt-up construction"] | ["Large fenced paved yard", "8 dock-high loading doors", "Calculated fire sprinkler system", "600 amp, 277/480 volt power", "18-foot clear height", "2,000 SF office space", "Office HVAC with heat and air conditioning", "56 parking spaces", "2 restrooms", "Easy access to I-5, SR-91, I-605, and SR-57"] |
| amenities | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | ["Utilities at the property", "3,273 feet of frontage along southbound I-45", "2,416 feet of frontage along FM-2004", "I-45 entrance in front of the property"] | ["Utilities at the property", "3,273 feet of frontage along southbound I-45", "2,416 feet of frontage along FM 2004"] |
| amenities | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | ["Excellent Street to Alley Access", "Huge Secured Concrete Yard", "Kitchenette", "Convenient Access to the 91 and 710 Freeways"] | ["±14,976 SF contractor's yard", "±2,702 SF freestanding office/shop building", "Street-to-alley access", "Secured concrete yard", "Fenced yard", "Kitchenette", "Access to the 91 and 710 freeways", "12-foot clear height", "2 ground-level doors", "4 parking spaces", "1 restroom"] |
| condition | gs01_33 Unit Multifamily Development.pdf | new_build | unknown |
| condition | gs06_8000 Wisconsin Avenue.pdf | under_construction | unknown |
| condition | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | unknown |
| floors_total | gs03_849+N+Bunker+Hill+OM.pdf | 12 | 6 |
| floors_total | gs10_document.pdf | 3 | null |
| location.state | gs01_33 Unit Multifamily Development.pdf | CO | US-CO |
| location.state | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | CA | US-CA |
| location.state | gs03_849+N+Bunker+Hill+OM.pdf | CA | US-CA |
| location.state | gs04_5623+Meridian+Los+Angeles.pdf | CA | US-CA |
| location.state | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | CA | US-CA |
| location.state | gs10_document.pdf | CA | US-CA |
| location.state | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | TX | US-TX |
| location.state | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | CA | US-CA |
| location.street1 | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | 6535 OASIS AVENUE | 6563 Oasis Avenue |
| name | gs01_33 Unit Multifamily Development.pdf | 33 Unit Multifamily Development | null |
| name | gs03_849+N+Bunker+Hill+OM.pdf | Bunker Height's Apartment Homes | Bunker Height’s Apartment Homes |
| seller | gs10_document.pdf | TheAgencyRE | The Agency |
| size.units | gs01_33 Unit Multifamily Development.pdf | 33 | null |
| total_price.period | gs06_8000 Wisconsin Avenue.pdf | one_time | null |
| total_price.period | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | one_time |
| type | gs06_8000 Wisconsin Avenue.pdf | multifamily/mixed_use | land |
| type | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | industrial | warehouse |
| type | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | Warehouse/Office | industrial |
| type_other | gs02_708-712+New+Depot+St+Bunker+Hill+Construction+OM.pdf | null | Multifamily |
| type_other | gs03_849+N+Bunker+Hill+OM.pdf | null | Apartment building |
| type_other | gs04_5623+Meridian+Los+Angeles.pdf | null | Multifamily |
| type_other | gs05_6563 OASIS AVENUE - TWENTYNINE PALMS, CA 92277.pdf | null | Multifamily |
| type_other | gs06_8000 Wisconsin Avenue.pdf | null | Mixed Use Multifamily Development Opportunity |
| type_other | gs10_document.pdf | null | Art gallery / commercial building |
| type_other | gs7_a3a5f396-7f32-4b27-bec3-6d8a06525a08.pdf | null | Free Standing Warehouse/Distribution Building |
| type_other | gs8_COMMGATE FLYER 67.0 acres I-45 and FM 2004.pdf | null | Land |
| type_other | gs9_16213-Illinois-Ave-AIR-Listing-Brochure-Industrial-for-Lease-1.pdf | null | Warehouse/Office |
