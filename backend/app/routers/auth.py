"""Login, current user, and a role-check example."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import schemas_auth as s
from app.database import get_db
from app.security import (TOKEN_MINUTES, create_token, get_current_user,
                          require_roles, verify_password)

router = APIRouter(prefix="/api", tags=["Auth"])


@router.post("/auth/login", response_model=s.TokenOut)
def login(body: s.LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        text("SELECT user_id, password_hash, role, is_active "
             "FROM app_user WHERE username = :u"),
        {"u": body.username},
    ).mappings().first()
    # One message for every failure, so attackers can't learn which usernames exist.
    if (user is None or not user["is_active"]
            or not verify_password(body.password, user["password_hash"])):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        db.execute(text("UPDATE app_user SET last_login_at = now() WHERE user_id = :id"),
                   {"id": user["user_id"]})
        db.commit()
    except SQLAlchemyError:
        db.rollback()  # a failed timestamp update should not block login
    return {"access_token": create_token(user["user_id"], user["role"]),
            "token_type": "bearer", "role": user["role"],
            "expires_in_minutes": TOKEN_MINUTES}


@router.get("/auth/me", response_model=s.UserOut)
def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/auth/admin-check")
def admin_check(user: dict = Depends(require_roles("ADMIN"))):
    """Only ADMIN gets through. Used to test role checks."""
    return {"message": "You are an admin", "username": user["username"]}