from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session


def get_latest_prices_by_region(db: Session, region_psgc: str) -> list:
    """Return the most recent price record per fuel type for all cities in a region."""
    from storage.models import PriceRecords  # type: ignore[attr-defined]

    subq = (
        select(
            PriceRecords.fuel_type,
            PriceRecords.psgc_code,
        )
        .where(PriceRecords.psgc_code.like(f"{region_psgc[:2]}%"))
        .order_by(PriceRecords.effective_date.desc())
        .distinct(PriceRecords.fuel_type, PriceRecords.psgc_code)
        .subquery()
    )

    stmt = (
        select(PriceRecords)
        .join(
            subq,
            (PriceRecords.fuel_type == subq.c.fuel_type)
            & (PriceRecords.psgc_code == subq.c.psgc_code),
        )
        .order_by(PriceRecords.effective_date.desc())
    )
    return db.execute(stmt).scalars().all()


def get_price_history(
    db: Session,
    region_psgc: str,
    fuel_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list:
    from storage.models import PriceRecords  # type: ignore[attr-defined]

    stmt = select(PriceRecords).where(
        PriceRecords.psgc_code.like(f"{region_psgc[:2]}%")
    )

    if fuel_type:
        stmt = stmt.where(PriceRecords.fuel_type == fuel_type)
    if from_date:
        stmt = stmt.where(PriceRecords.effective_date >= from_date)
    if to_date:
        stmt = stmt.where(PriceRecords.effective_date <= to_date)

    stmt = stmt.order_by(PriceRecords.effective_date.asc())
    return db.execute(stmt).scalars().all()
