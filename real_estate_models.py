from typing import Literal, Optional

from pydantic import BaseModel, Field


DealType = Literal["sale", "lease", "other"]
PropertyType = Literal[
    "land",
    "residential",
    "commercial",
    "industrial",
    "mixed_use",
    "office",
    "retail",
    "building",
    "hotel",
    "warehouse",
    "agricultural",
    "other",
]
Condition = Literal[
    "new_build",
    "under_construction",
    "renovated",
    "needs_renovation",
    "unknown",
]
PricePeriod = Literal["monthly", "yearly", "one_time"]


class Price(BaseModel):
    per_sf: Optional[float] = None
    per_sf_currency: Optional[str] = None
    per_unit: Optional[float] = None
    per_unit_currency: Optional[str] = None


class TotalPrice(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[PricePeriod] = None


class PropertySize(BaseModel):
    sf: Optional[float] = None
    units: Optional[float] = None
    acreage: Optional[float] = None
    sqm: Optional[float] = None
    hectares: Optional[float] = None


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    street1: Optional[str] = None
    street2: Optional[str] = None


class RealEstateListing(BaseModel):
    name: Optional[str] = None
    deal_type: Optional[DealType] = None
    type: Optional[PropertyType] = None
    type_other: Optional[str] = None
    price: Optional[Price] = None
    total_price: Optional[TotalPrice] = None
    size: Optional[PropertySize] = None
    amenities: list[str] = Field(default_factory=list)
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    condition: Optional[Condition] = None
    location: Optional[Location] = None
    seller: Optional[str] = None


class ListingRecord(BaseModel):
    source_file: str
    expected: RealEstateListing