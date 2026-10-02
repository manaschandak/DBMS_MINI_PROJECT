"""Analytics: read-only endpoints built on the database views."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def rows(db: Session, sql: str):
    """Run a read-only query and return a list of dicts."""
    try:
        return [dict(r) for r in db.execute(text(sql)).mappings().all()]
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database error")


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Fleet summary: batteries by status, risk distribution, open alerts."""
    by_status = rows(db, "SELECT status, count(*) AS count FROM battery GROUP BY status ORDER BY status")
    risk = rows(db, "SELECT risk_type, final_risk_level, battery_count FROM v_risk_distribution "
                    "ORDER BY risk_type, final_risk_level")
    alerts = rows(db, "SELECT priority_code, severity_level, count(*) AS count FROM v_open_alerts "
                      "GROUP BY priority_code, severity_level ORDER BY severity_level")
    return {
        "totals": {
            "batteries": sum(r["count"] for r in by_status),
            "open_alerts": sum(r["count"] for r in alerts),
        },
        "batteries_by_status": by_status,
        "risk_distribution": risk,
        "open_alerts_by_priority": alerts,
    }


@router.get("/batteries")
def battery_overview(db: Session = Depends(get_db)):
    """One row per battery: latest temperature, risk levels, open alerts."""
    return rows(db, "SELECT * FROM v_battery_overview ORDER BY battery_id")


@router.get("/open-alerts")
def open_alerts(db: Session = Depends(get_db)):
    """Open alerts, most severe first."""
    return rows(db, "SELECT * FROM v_open_alerts ORDER BY severity_level DESC, created_at DESC")


@router.get("/chemistry-comparison")
def chemistry_comparison(db: Session = Depends(get_db)):
    """NMC vs LFP vs NCA, straight from the comparison view."""
    return rows(db, "SELECT * FROM v_chemistry_comparison ORDER BY chemistry_code")


@router.get("/manufacturer-comparison")
def manufacturer_comparison(db: Session = Depends(get_db)):
    """Same idea by manufacturer. LEFT JOINs keep manufacturers that have no data yet."""
    return rows(db,
        "SELECT m.manufacturer_id, m.manufacturer_name, "
        "count(DISTINCT b.battery_id) AS battery_count, "
        "ROUND(AVG(a.cycle_count), 1) AS avg_cycles, "
        "ROUND(AVG(a.internal_resistance_mohm), 3) AS avg_resistance_mohm, "
        "ROUND(AVG(a.capacity_ah / b.nominal_capacity_ah * 100), 2) AS avg_capacity_pct_of_nominal "
        "FROM manufacturer m "
        "LEFT JOIN battery b ON b.manufacturer_id = m.manufacturer_id "
        "LEFT JOIN aging_record a ON a.battery_id = b.battery_id "
        "GROUP BY m.manufacturer_id, m.manufacturer_name "
        "ORDER BY m.manufacturer_id")


@router.get("/model-accuracy")
def model_accuracy(db: Session = Depends(get_db)):
    """Live accuracy of each AI model against recorded feedback."""
    return rows(db, "SELECT * FROM v_live_accuracy ORDER BY model_id, risk_type")