"""Batteries: list, view, register, update, delete."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Batteries"])

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
CHECK_VIOLATION = "23514"

# One query used everywhere, so every response has the same shape.
# JOINs add the manufacturer name and chemistry code to each battery.
BATTERY_SELECT = (
    "SELECT b.battery_id, b.serial_number, b.battery_type, "
    "b.manufacturer_id, m.manufacturer_name, "
    "b.chemistry_id, c.chemistry_code, "
    "b.nominal_capacity_ah, b.install_date, b.status "
    "FROM battery b "
    "JOIN manufacturer m ON m.manufacturer_id = b.manufacturer_id "
    "JOIN chemistry c ON c.chemistry_id = b.chemistry_id"
)


def pg_code(exc: IntegrityError):
    return getattr(exc.orig, "sqlstate", None)


def fetch_battery(db: Session, battery_id: int):
    return db.execute(
        text(BATTERY_SELECT + " WHERE b.battery_id = :id"), {"id": battery_id}
    ).mappings().first()


def explain_integrity_error(exc: IntegrityError, action: str):
    code = pg_code(exc)
    if code == UNIQUE_VIOLATION:
        return HTTPException(status_code=409, detail="A battery with this serial number already exists")
    if code == FOREIGN_KEY_VIOLATION:
        return HTTPException(status_code=422, detail="manufacturer_id or chemistry_id does not exist")
    if code == CHECK_VIOLATION:
        return HTTPException(status_code=422, detail="A value is outside the allowed range")
    return HTTPException(status_code=400, detail=f"Could not {action} the battery")


@router.get("/batteries", response_model=list[schemas.BatteryOut])
def list_batteries(db: Session = Depends(get_db)):
    return db.execute(text(BATTERY_SELECT + " ORDER BY b.battery_id")).mappings().all()


@router.get("/batteries/{battery_id}", response_model=schemas.BatteryOut)
def get_battery(battery_id: int, db: Session = Depends(get_db)):
    row = fetch_battery(db, battery_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Battery not found")
    return row


@router.post("/batteries", response_model=schemas.BatteryOut,
             status_code=status.HTTP_201_CREATED)
def create_battery(body: schemas.BatteryCreate, db: Session = Depends(get_db)):
    try:
        new_id = db.execute(
            text("INSERT INTO battery (serial_number, battery_type, manufacturer_id, "
                 "chemistry_id, nominal_capacity_ah, install_date, status) "
                 "VALUES (:serial, :btype, :mid, :cid, :cap, :inst, :status) "
                 "RETURNING battery_id"),
            {"serial": body.serial_number, "btype": body.battery_type,
             "mid": body.manufacturer_id, "cid": body.chemistry_id,
             "cap": body.nominal_capacity_ah, "inst": body.install_date,
             "status": body.status},
        ).scalar_one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise explain_integrity_error(exc, "save")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return fetch_battery(db, new_id)


@router.put("/batteries/{battery_id}", response_model=schemas.BatteryOut)
def update_battery(battery_id: int, body: schemas.BatteryCreate,
                   db: Session = Depends(get_db)):
    try:
        updated = db.execute(
            text("UPDATE battery SET serial_number = :serial, battery_type = :btype, "
                 "manufacturer_id = :mid, chemistry_id = :cid, "
                 "nominal_capacity_ah = :cap, install_date = :inst, status = :status "
                 "WHERE battery_id = :id RETURNING battery_id"),
            {"serial": body.serial_number, "btype": body.battery_type,
             "mid": body.manufacturer_id, "cid": body.chemistry_id,
             "cap": body.nominal_capacity_ah, "inst": body.install_date,
             "status": body.status, "id": battery_id},
        ).first()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise explain_integrity_error(exc, "update")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    if updated is None:
        raise HTTPException(status_code=404, detail="Battery not found")
    return fetch_battery(db, battery_id)


@router.delete("/batteries/{battery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_battery(battery_id: int, db: Session = Depends(get_db)):
    try:
        deleted = db.execute(
            text("DELETE FROM battery WHERE battery_id = :id RETURNING battery_id"),
            {"id": battery_id},
        ).first()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=409,
                                detail="Cannot delete: sensors, aging records or predictions still reference this battery")
        raise HTTPException(status_code=400, detail="Could not delete the battery")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    if deleted is None:
        raise HTTPException(status_code=404, detail="Battery not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)