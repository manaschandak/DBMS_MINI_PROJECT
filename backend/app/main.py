"""FastAPI entry point."""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import batteries, reference, sensors, twins

app = FastAPI(title="Battery Thermal Management API", version="0.1.0")

# Lets the React dev server (Vite's default port) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reference.router)
app.include_router(batteries.router)
app.include_router(sensors.router)
app.include_router(twins.router)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    """Proves the API is up AND can reach the database."""
    try:
        tables = db.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
        ).scalar()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "ok", "database": "connected", "tables": tables}