from datetime import date, datetime

from pydantic import BaseModel


class PriceRecordResponse(BaseModel):
    id: str
    effective_date: date
    psgc_code: str | None
    fuel_type: str
    price_php_per_liter: float
    raw_location: str | None
    ingested_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    detail: str
