"""Reference data: manufacturers and chemistries."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Reference data"])

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"


def pg_code(exc: IntegrityError):
    """PostgreSQL's error code, e.g. 23505 = duplicate value."""
    return getattr(exc.orig, "sqlstate", None)


# ---------------- Manufacturers ----------------

@router.get("/manufacturers", response_model=list[schemas.ManufacturerOut])
def list_manufacturers(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT manufacturer_id, manufacturer_name, created_at "
             "FROM manufacturer ORDER BY manufacturer_id")
    ).mappings().all()
    return rows


@router.post("/manufacturers", response_model=schemas.ManufacturerOut,
             status_code=status.HTTP_201_CREATED)
def create_manufacturer(body: schemas.ManufacturerCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("INSERT INTO manufacturer (manufacturer_name) VALUES (:name) "
                 "RETURNING manufacturer_id, manufacturer_name, created_at"),
            {"name": body.manufacturer_name},
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409, detail="A manufacturer with this name already exists")
        raise HTTPException(status_code=400, detail="Could not save the manufacturer")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return row


@router.put("/manufacturers/{manufacturer_id}", response_model=schemas.ManufacturerOut)
def update_manufacturer(manufacturer_id: int, body: schemas.ManufacturerCreate,
                        db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("UPDATE manufacturer SET manufacturer_name = :name "
                 "WHERE manufacturer_id = :id "
                 "RETURNING manufacturer_id, manufacturer_name, created_at"),
            {"name": body.manufacturer_name, "id": manufacturer_id},
        ).mappings().first()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409, detail="A manufacturer with this name already exists")
        raise HTTPException(status_code=400, detail="Could not update the manufacturer")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    if row is None:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return row


@router.delete("/manufacturers/{manufacturer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    try:
        deleted = db.execute(
            text("DELETE FROM manufacturer WHERE manufacturer_id = :id "
                 "RETURNING manufacturer_id"),
            {"id": manufacturer_id},
        ).first()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == FOREIGN_KEY_VIOLATION:
            raise HTTPException(status_code=409,
                                detail="Cannot delete: batteries still reference this manufacturer")
        raise HTTPException(status_code=400, detail="Could not delete the manufacturer")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    if deleted is None:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------- Chemistries ----------------

@router.get("/chemistries", response_model=list[schemas.ChemistryOut])
def list_chemistries(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT chemistry_id, chemistry_code, chemistry_name "
             "FROM chemistry ORDER BY chemistry_id")
    ).mappings().all()
    return rows


@router.post("/chemistries", response_model=schemas.ChemistryOut,
             status_code=status.HTTP_201_CREATED)
def create_chemistry(body: schemas.ChemistryCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("INSERT INTO chemistry (chemistry_code, chemistry_name) "
                 "VALUES (:code, :name) "
                 "RETURNING chemistry_id, chemistry_code, chemistry_name"),
            {"code": body.chemistry_code.upper(), "name": body.chemistry_name},
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if pg_code(exc) == UNIQUE_VIOLATION:
            raise HTTPException(status_code=409, detail="A chemistry with this code already exists")
        raise HTTPException(status_code=400, detail="Could not save the chemistry")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database error")
    return row