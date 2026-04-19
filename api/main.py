from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy.orm import Session

from .auth import verify_auth
from .database import check_db_connection, get_db
from .schemas import ErrorResponse, HealthResponse, PriceRecordResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import _engine  # noqa: F401

    yield
    _engine.dispose()


app = FastAPI(
    title="PH Fuel Price Tracker API",
    description="Query weekly retail fuel pump prices from the Philippine Department of Energy.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "/openapi.json", title=app.title
    )


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    if check_db_connection():
        return HealthResponse(status="ok")
    return HealthResponse(status="degraded", detail="Database unreachable")


@app.get(
    "/prices/latest",
    response_model=list[PriceRecordResponse],
    responses={404: {"model": ErrorResponse}},
    tags=["prices"],
    dependencies=[Depends(verify_auth)],
)
async def latest_prices(
    region: str = Query(..., description="Region PSGC code (e.g. 130000000 for NCR)"),
    db: Session = Depends(get_db),
) -> list[PriceRecordResponse]:
    from storage.queries import get_latest_prices_by_region

    records = get_latest_prices_by_region(db, region)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for region {region}",
        )
    return [PriceRecordResponse.model_validate(r) for r in records]


@app.get(
    "/prices",
    response_model=list[PriceRecordResponse],
    responses={422: {"model": ErrorResponse}},
    tags=["prices"],
    dependencies=[Depends(verify_auth)],
)
async def price_history(
    region: str = Query(..., description="Region PSGC code"),
    fuel_type: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
) -> list[PriceRecordResponse]:
    from storage.queries import get_price_history

    records = get_price_history(db, region, fuel_type, from_date, to_date)
    return [PriceRecordResponse.model_validate(r) for r in records]
