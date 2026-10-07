"""Digital twins and CFD simulations."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_twins as t
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Digital twin and CFD"])

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
CHECK_VIOLATION = "23514"

TWIN_COLS = "twin_id, battery_id, model_version, last_synced_at, simulated_soh_pct"
CFD_COLS = ("simulation_id, twin_id, run_at, flow_rate_lpm, inlet_temp_c, "
            "max_temp_c, avg_temp_c, pressure_drop_kpa, data_source_id")


def pg_code(exc: IntegrityError):
    return getattr(exc.orig, "sqlstate", None)


# ---------------- Digital twins ----------------

@router.get("/digital-twins", response_model=list[t.TwinOut])
def list_twins(db: Session = Depends(get_db)):
    return db.execute(
        text(f"SELECT {TWIN_COLS} FROM digital_twin ORDER BY twin_id")
    ).mappings().all()


@router.post("/digital-twins", response_model=t.TwinOut,
             status_code=status.HTTP_201_CREATED)
def create_twin(body: t.TwinCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("INSERT INTO digital_twin (battery_id, model_version, last_synced_at, simulated_soh_pct) "
                 "VALUES (:bid, :ver, :synced, :soh) "
                 f"RETURNING {TWIN_COLS}"),
            {"bid": body.battery_id, "ver": body.model_version,
             "synced": body.last_synced_at, "soh": body.simulated_soh_pct},
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        code = pg_code(exc)
        if code == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409, detail="This battery already has a digital twin")
        if code == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=422, detail="battery_id does not exist")
        if code == CHECK_VIOLATION:
            raise HTTPException(status_code=422, detail="A value is outside the allowed range")
        raise HTTPException(status_code=400, detail="Could not save the digital twin")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return row


@router.get("/batteries/{battery_id}/twin", response_model=t.TwinDetail)
def get_battery_twin(battery_id: int, db: Session = Depends(get_db)):
    """A battery's twin together with all its CFD simulations, newest first."""
    if db.execute(text("SELECT 1 FROM battery WHERE battery_id = :id"),
                  {"id": battery_id}).first() is None:
        raise HTTPException(status_code=404, detail="Battery not found")
    twin = db.execute(
        text(f"SELECT {TWIN_COLS} FROM digital_twin WHERE battery_id = :id"),
        {"id": battery_id},
    ).mappings().first()
    if twin is None:
        raise HTTPException(status_code=404, detail="This battery has no digital twin")
    sims = db.execute(
        text(f"SELECT {CFD_COLS} FROM cfd_simulation WHERE twin_id = :tid "
             "ORDER BY run_at DESC"),
        {"tid": twin["twin_id"]},
    ).mappings().all()
    return {**dict(twin), "simulations": [dict(r) for r in sims]}


# ---------------- CFD simulations ----------------

@router.get("/cfd-simulations", response_model=list[t.CfdOut])
def list_cfd(twin_id: Optional[int] = Query(None, gt=0), db: Session = Depends(get_db)):
    if twin_id is None:
        return db.execute(
            text(f"SELECT {CFD_COLS} FROM cfd_simulation ORDER BY simulation_id")
        ).mappings().all()
    return db.execute(
        text(f"SELECT {CFD_COLS} FROM cfd_simulation WHERE twin_id = :tid "
             "ORDER BY run_at DESC"),
        {"tid": twin_id},
    ).mappings().all()


@router.post("/cfd-simulations", response_model=t.CfdOut,
             status_code=status.HTTP_201_CREATED)
def create_cfd(body: t.CfdCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("INSERT INTO cfd_simulation (twin_id, run_at, flow_rate_lpm, inlet_temp_c, "
                 "max_temp_c, avg_temp_c, pressure_drop_kpa, data_source_id) "
                 "VALUES (:tid, COALESCE(CAST(:run_at AS timestamptz), now()), :flow, :inlet, "
                 ":tmax, :tavg, :dp, :dsid) "
                 f"RETURNING {CFD_COLS}"),
            {"tid": body.twin_id, "run_at": body.run_at, "flow": body.flow_rate_lpm,
             "inlet": body.inlet_temp_c, "tmax": body.max_temp_c, "tavg": body.avg_temp_c,
             "dp": body.pressure_drop_kpa, "dsid": body.data_source_id},
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        code = pg_code(exc)
        if code == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=422, detail="twin_id or data_source_id does not exist")
        if code == CHECK_VIOLATION:
            raise HTTPException(status_code=422, detail="A value is outside the allowed range")
        raise HTTPException(status_code=400, detail="Could not save the simulation")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return row