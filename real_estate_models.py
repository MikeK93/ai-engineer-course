"""Schema for extracting structured data from commercial real estate listings.

If the source text does not state a field, return None. Never guess.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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
    per_sf: Optional[float] = Field(None, description="Price per square foot")
    per_sf_currency: Optional[str] = Field(
        None, description="ISO 4217 currency code for the per-square-foot price"
    )
    per_unit: Optional[float] = Field(None, description="Price per unit")
    per_unit_currency: Optional[str] = Field(
        None, description="ISO 4217 currency code for the per-unit price"
    )


class TotalPrice(BaseModel):
    label: Optional[str] = Field(
        None, description="Text such as 'Negotiable' when no numeric price is stated if available instead of the actual price"
    )
    amount: Optional[float] = Field(None, description="Numeric total price only")
    currency: Optional[str] = Field(None, description="ISO 4217 currency code")
    period: Optional[PricePeriod] = Field(
        None, description="Time period or payment basis for the total price"
    )


class PropertySize(BaseModel):
    sf: Optional[float] = Field(None, description="Area in square feet")
    units: Optional[float] = Field(None, description="Number of property units")
    acreage: Optional[float] = Field(None, description="Area in acres")
    sqm: Optional[float] = Field(None, description="Area in square meters")
    hectares: Optional[float] = Field(None, description="Area in hectares")


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = Field(None, description="State, province, or region")
    country: Optional[str] = None
    zip: Optional[str] = None
    street1: Optional[str] = Field(None, description="Street address as written")
    street2: Optional[str] = Field(None, description="Additional address details")


class RealEstateListing(BaseModel):
    name: Optional[str] = Field(None, description="Property or listing name as written")
    deal_type: Optional[DealType] = Field(None, description="Sale, lease, or other")
    type: Optional[PropertyType] = Field(
        None, description="Best matching property category; use 'other' if none fits"
    )
    type_other: Optional[str] = Field(
        None, description="Property category details when stated"
    )
    price: Optional[Price] = None
    total_price: Optional[TotalPrice] = None
    size: Optional[PropertySize] = None
    amenities: list[str] = Field(
        default_factory=list, description="Stated amenities; empty list if none are stated"
    )
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    condition: Optional[Condition] = None
    location: Optional[Location] = None
    seller: Optional[str] = Field(None, description="Broker or seller as written")


class ListingRecord(BaseModel):
    source_file: str
    expected: RealEstateListing