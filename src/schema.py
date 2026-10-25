"""Schema for extracting structured data from commercial real estate listings.

If the source text does not state a field, return None. Never guess.
"""

from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field

# int-or-float so whole numbers serialize without a trailing ".0"
Number = Union[int, float]


class DealType(str, Enum):
    sale = "sale"
    lease = "lease"
    other = "other"


class PropertyType(str, Enum):
    multifamily = "multifamily"
    office = "office"
    retail = "retail"
    industrial = "industrial"
    hospitality = "hospitality"
    mixed_use = "mixed_use"
    multifamily_mixed_use = "multifamily/mixed_use"
    land = "land"
    residential = "residential"
    commercial = "commercial"
    building = "building"
    hotel = "hotel"
    warehouse = "warehouse"
    agricultural = "agricultural"
    other = "other"


class Condition(str, Enum):
    new_build = "new_build"
    under_construction = "under_construction"
    renovated = "renovated"
    needs_renovation = "needs_renovation"
    unknown = "unknown"


class PricePeriod(str, Enum):
    monthly = "monthly"
    yearly = "yearly"
    one_time = "one_time"


class Price(BaseModel):
    per_sf: Optional[Number] = Field(None, description="Price per square foot")
    per_sf_currency: Optional[str] = Field(
        None, description="ISO 4217 currency code for the per-square-foot price"
    )
    per_unit: Optional[Number] = Field(None, description="Price per unit")
    per_unit_currency: Optional[str] = Field(
        None, description="ISO 4217 currency code for the per-unit price"
    )


class TotalPrice(BaseModel):
    label: Optional[str] = Field(
        None, description="Text such as 'Negotiable' when no numeric price is stated if available instead of the actual price"
    )
    amount: Optional[Number] = Field(None, description="Numeric total price only. AKA asking price for the listed property.")
    currency: Optional[str] = Field(None, description="ISO 4217 currency code")
    period: Optional[PricePeriod] = Field(
        None, description="Time period or payment basis for the total price"
    )


class PropertySize(BaseModel):
    sf: Optional[Number] = Field(None, description="Area in square feet. Aka Lot size.")
    units: Optional[Number] = Field(None, description="Number of property units")
    acreage: Optional[Number] = Field(None, description="Area in acres")
    sqm: Optional[Number] = Field(None, description="Area in square meters")
    hectares: Optional[Number] = Field(None, description="Area in hectares")


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = Field(None, description="State, province, or region. Use ISO 3166-2 code.")
    country: Optional[str] = Field(
        None,
        description="Country; infer from other address fields when possible, but use None if it cannot be determined. Use ISO 3166-1 alpha-2 code.",
    )
    zip: Optional[str] = None
    street1: Optional[str] = Field(None, description="Street address as written")
    street2: Optional[str] = Field(None, description="Additional address details")


class RealEstateListing(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Property name as written, if stated; otherwise leave None. Do not use the address as the name. Property name can be near the address on the first page or at Property Overview section when available.",
    )
    deal_type: Optional[DealType] = Field(None, description="Sale, lease, or both")
    type: Optional[PropertyType] = Field(
        None,
        description="Best matching property category; use 'other' if none fits. Actual type of the listed property. Do not consider future plan for the property (e.g. Land -> Multifamily, etc.).",
    )
    type_other: Optional[str] = Field(
        None,
        description="Property category details when stated. The raw value of property type after mapping to type enum.",
    )
    price: Optional[Price] = None
    total_price: Optional[TotalPrice] = Field(None, description="Asking price.")
    size: Optional[PropertySize] = Field(
        None, description="Property lot size in square feet."
    ),
    amenities: list[str] = Field(
        default_factory=list, description="Stated amenities; empty list if none are stated"
    )
    floor: Optional[int] = None
    floors_total: Optional[int] = Field(None,
        description="Total number of floors (sometimes referred to as stories). If no explicit mention of total floors, check Floor Plans section when available."
    )
    condition: Optional[Condition] = Field(
        None, description="If not specified explicitly, infer from content. If no candidates fallback to unknown."
    )
    location: Optional[Location] = None
    seller: Optional[str] = Field(None, description="Broker or seller as written. Company name -> Broker.")


class ListingRecord(BaseModel):
    source_file: str
    expected: RealEstateListing