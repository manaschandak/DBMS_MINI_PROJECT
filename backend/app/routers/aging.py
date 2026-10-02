"""Aging records: history, latest, add."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_aging as a
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Aging"])

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
CHECK_VIOLATION = "23514"

# JOIN battery to compute state of health from the nominal capacity.
AGING_SELECT = (
    "SELECT a.aging_id, a.battery_id, a.measured_at, a.cycle_count, "
    "a.calendar_age_days, a.capacity_ah, a.internal_resistance_mohm, "
    "a.data_source_id, "
    "ROUND(a.capacity_ah / b.nominal_capacity_ah * 100, 2) AS soh_pct "
    "FROM aging_record a JOIN battery b ON b.battery_id = a.battery_id"
)


def pg_code(exc: IntegrityError):
    return getattr(exc.orig, "sqlstate", None)


def require_battery(db: Session, battery_id: int):
    if db.execute(text("SELECT 1 FROM battery WHERE battery_id = :id"),
                  {"id": battery_id}).first() is None:
        raise HTTPException(status_code=404, detail="Battery not found")


@router.get("/batteries/{battery_id}/aging", response_model=list[a.AgingOut])
def list_aging(
    battery_id: int,
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    require_battery(db, battery_id)
    where = ["a.battery_id = :id"]
    params = {"id": battery_id, "limit": limit}
    if date_from is not None:
        where.append("a.measured_at >= :d_from")
        params["d_from"] = date_from
    if date_to is not None:
        where.append("a.measured_at <= :d_to")
        params["d_to"] = date_to
    return db.execute(
        text(AGING_SELECT + " WHERE " + " AND ".join(where) +
             " ORDER BY a.measured_at DESC LIMIT :limit"),
        params,
    ).mappings().all()


@router.get("/batteries/{battery_id}/aging/latest", response_model=a.AgingOut)
def latest_aging(battery_id: int, db: Session = Depends(get_db)):
    require_battery(db, battery_id)
    row = db.execute(
        text(AGING_SELECT + " WHERE a.battery_id = :id "
             "ORDER BY a.measured_at DESC LIMIT 1"),
        {"id": battery_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="This battery has no aging records")
    return row


@router.post("/batteries/{battery_id}/aging", response_model=a.AgingOut,
             status_code=status.HTTP_201_CREATED)
def create_aging(battery_id: int, body: a.AgingCreate, db: Session = Depends(get_db)):
    require_battery(db, battery_id)
    try:
        new_id = db.execute(
            text("INSERT INTO aging_record (battery_id, measured_at, cycle_count, "
                 "calendar_age_days, capacity_ah, internal_resistance_mohm, data_source_id) "
                 "VALUES (:bid, :at, :cycles, :days, :cap, :res, :dsid) "
                 "RETURNING aging_id"),
            {"bid": battery_id, "at": body.measured_at, "cycles": body.cycle_count,
             "days": body.calendar_age_days, "cap": body.capacity_ah,
             "res": body.internal_resistance_mohm, "dsid": body.data_source_id},
        ).scalar_one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        code = pg_code(exc)
        if code == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409,
                                detail="This battery already has an aging record at that time")
        if code == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=422, detail="data_source_id does not exist")
        if code == CHECK_VIOLATION:
            raise HTTPException(status_code=422, detail="A value is outside the allowed range")
        raise HTTPException(status_code=400, detail="Could not save the aging record")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return db.execute(
        text(AGING_SELECT + " WHERE a.aging_id = :id"), {"id": new_id}
    ).mappings().one()