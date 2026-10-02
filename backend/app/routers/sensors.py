"""Sensors and readings."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_sensors as s
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Sensors and readings"])

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
CHECK_VIOLATION = "23514"

# Which sensor type each kind of reading needs, and how to read it back.
TYPE_FOR = {"temperature": "TEMPERATURE", "electrical": "ELECTRICAL", "coolant": "COOLANT_FLOW"}
READ_TABLE = {
    "TEMPERATURE": ("temperature_reading", "sensor_id, recorded_at, temperature_c, data_source_id"),
    "ELECTRICAL": ("electrical_reading", "sensor_id, recorded_at, voltage_v, current_a, data_source_id"),
    "COOLANT_FLOW": ("coolant_flow", "sensor_id, recorded_at, flow_rate_lpm, inlet_temp_c, data_source_id"),
}
INSERT_SQL = {
    "temperature": "INSERT INTO temperature_reading (sensor_id, recorded_at, temperature_c, data_source_id) "
                   "VALUES (:sensor_id, :recorded_at, :temperature_c, :data_source_id)",
    "electrical": "INSERT INTO electrical_reading (sensor_id, recorded_at, voltage_v, current_a, data_source_id) "
                  "VALUES (:sensor_id, :recorded_at, :voltage_v, :current_a, :data_source_id)",
    "coolant": "INSERT INTO coolant_flow (sensor_id, recorded_at, flow_rate_lpm, inlet_temp_c, data_source_id) "
               "VALUES (:sensor_id, :recorded_at, :flow_rate_lpm, :inlet_temp_c, :data_source_id)",
}


def pg_code(exc: IntegrityError):
    return getattr(exc.orig, "sqlstate", None)


def battery_exists(db: Session, battery_id: int) -> bool:
    return db.execute(
        text("SELECT 1 FROM battery WHERE battery_id = :id"), {"id": battery_id}
    ).first() is not None


# ---------------- Sensors ----------------

@router.get("/batteries/{battery_id}/sensors", response_model=list[s.SensorOut])
def list_sensors(battery_id: int, db: Session = Depends(get_db)):
    if not battery_exists(db, battery_id):
        raise HTTPException(status_code=404, detail="Battery not found")
    return db.execute(
        text("SELECT sensor_id, battery_id, sensor_type, location, is_active "
             "FROM sensor WHERE battery_id = :id ORDER BY sensor_id"),
        {"id": battery_id},
    ).mappings().all()


@router.post("/batteries/{battery_id}/sensors", response_model=s.SensorOut,
             status_code=status.HTTP_201_CREATED)
def create_sensor(battery_id: int, body: s.SensorCreate, db: Session = Depends(get_db)):
    if not battery_exists(db, battery_id):
        raise HTTPException(status_code=404, detail="Battery not found")
    try:
        row = db.execute(
            text("INSERT INTO sensor (battery_id, sensor_type, location, is_active) "
                 "VALUES (:bid, :stype, :loc, :active) "
                 "RETURNING sensor_id, battery_id, sensor_type, location, is_active"),
            {"bid": battery_id, "stype": body.sensor_type,
             "loc": body.location, "active": body.is_active},
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409, detail="This battery already has a sensor at that location")
        raise HTTPException(status_code=400, detail="Could not save the sensor")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return row


# ---------------- Readings ----------------

def check_sensor_types(db: Session, kind: str, rows: list):
    """Every sensor in a group must exist and be the right type."""
    ids = sorted({r["sensor_id"] for r in rows})
    if not ids:
        return
    found = db.execute(
        text("SELECT sensor_id FROM sensor WHERE sensor_id = ANY(:ids) AND sensor_type = :t"),
        {"ids": ids, "t": TYPE_FOR[kind]},
    ).scalars().all()
    bad = sorted(set(ids) - set(found))
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"{kind} readings need sensors of type {TYPE_FOR[kind]}; invalid sensor ids: {bad}",
        )


@router.post("/readings", status_code=status.HTTP_201_CREATED)
def insert_readings(body: s.ReadingsBatch, db: Session = Depends(get_db)):
    """All-or-nothing: one transaction for the whole batch."""
    groups = {
        "temperature": [r.model_dump() for r in body.temperature],
        "electrical": [r.model_dump() for r in body.electrical],
        "coolant": [r.model_dump() for r in body.coolant],
    }
    try:
        for kind, rows in groups.items():
            check_sensor_types(db, kind, rows)
        for kind, rows in groups.items():
            if rows:
                db.execute(text(INSERT_SQL[kind]), rows)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        code = pg_code(exc)
        if code == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409,
                                detail="A reading for that sensor and time already exists. Nothing was saved.")
        if code == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=422,
                                detail="sensor_id or data_source_id does not exist. Nothing was saved.")
        if code == CHECK_VIOLATION:
            raise HTTPException(status_code=422,
                                detail="A value is outside the allowed range. Nothing was saved.")
        raise HTTPException(status_code=400, detail="Could not save the readings. Nothing was saved.")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error. Nothing was saved.")
    return {"inserted": {kind: len(rows) for kind, rows in groups.items()}}


@router.get("/sensors/{sensor_id}/readings")
def get_readings(
    sensor_id: int,
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    sensor = db.execute(
        text("SELECT sensor_type FROM sensor WHERE sensor_id = :id"), {"id": sensor_id}
    ).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    table, columns = READ_TABLE[sensor.sensor_type]  # fixed names, not user input
    where = ["sensor_id = :id"]
    params = {"id": sensor_id, "limit": limit}
    if date_from is not None:
        where.append("recorded_at >= :d_from")
        params["d_from"] = date_from
    if date_to is not None:
        where.append("recorded_at <= :d_to")
        params["d_to"] = date_to

    rows = db.execute(
        text(f"SELECT {columns} FROM {table} WHERE {' AND '.join(where)} "
             "ORDER BY recorded_at DESC LIMIT :limit"),
        params,
    ).mappings().all()
    return {"sensor_id": sensor_id, "sensor_type": sensor.sensor_type,
            "count": len(rows), "readings": [dict(r) for r in rows]}