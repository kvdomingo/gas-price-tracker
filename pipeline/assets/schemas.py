from enum import StrEnum

from pydantic import BaseModel, Field


class FuelType(StrEnum):
    RON100 = "RON100"
    RON97 = "RON97"
    RON95 = "RON95"
    RON91 = "RON91"
    DIESEL = "DIESEL"
    DIESEL_PLUS = "DIESEL_PLUS"
    KEROSENE = "KEROSENE"


class FuelBrand(StrEnum):
    PETRON = "PETRON"
    SHELL = "SHELL"
    CALTEX = "CALTEX"
    PHOENIX = "PHOENIX"
    TOTAL = "TOTAL"
    FLYING_V = "FLYING_V"
    UNIOIL = "UNIOIL"
    SEAOIL = "SEAOIL"
    PTT = "PTT"
    INDEPENDENT = "INDEPENDENT"


class FuelPrice(BaseModel):
    area: str = Field(description="Name of the area/city")
    product: FuelType
    brand: FuelBrand
    min_price: float | None = Field(
        None,
        ge=0.0,
        description="Minimum of the price range for a single combination of product and brand",
    )
    max_price: float | None = Field(
        None,
        ge=0.0,
        description="Maximum of the price range for a single combination of product and brand",
    )
    overall_range_min: float | None = Field(
        None, ge=0.0, description="Minimum price indicated under 'OVERALL RANGE' column"
    )
    overall_range_max: float | None = Field(
        None, ge=0.0, description="Maximum price indicated under 'OVERALL RANGE' column"
    )
    common_price: float | None = Field(
        None, ge=0.0, description="Price indicated under 'COMMON PRICE' column"
    )


class FuelPricesGeminiStructuredOutput(BaseModel):
    results: list[FuelPrice]
