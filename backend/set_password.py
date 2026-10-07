"""Set a user's password (stored as a bcrypt hash).

Run from the project root:  python backend/set_password.py USERNAME
The password is typed hidden and is never saved anywhere in plain text.
"""
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.security import hash_password  # noqa: E402

if len(sys.argv) != 2:
    sys.exit("Usage: python backend\\set_password.py USERNAME")
username = sys.argv[1]

password = getpass("New password (min 8 characters, hidden): ")
if len(password) < 8 or len(password.encode("utf-8")) > 72:
    sys.exit("Password must be 8 to 72 characters.")
if password != getpass("Type it again: "):
    sys.exit("Passwords did not match. Nothing changed.")

with SessionLocal() as db:
    updated = db.execute(
        text("UPDATE app_user SET password_hash = :h WHERE username = :u RETURNING user_id"),
        {"h": hash_password(password), "u": username},
    ).first()
    db.commit()

print("Password updated for " + username if updated else "No such user: " + username)