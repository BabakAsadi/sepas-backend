"""Create the first administrator account from bootstrap environment variables."""

import sys
from sqlalchemy.exc import IntegrityError

from app.core.config import ADMIN_PASSWORD, BOOTSTRAP_ADMIN_USERNAME
from app.database.session import SessionLocal
from app.features.auth.model import User
from app.features.auth.service import hash_password
import app.database.models  # noqa: F401


def main() -> int:
    if not ADMIN_PASSWORD:
        print("ADMIN_PASSWORD is required in .env for initial admin creation.")
        return 1

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "admin").first()
        if existing:
            print(f"An administrator already exists (username: {existing.username}). No changes made.")
            return 0

        user = User(
            username=BOOTSTRAP_ADMIN_USERNAME.strip().lower(),
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Administrator '{user.username}' created successfully.")
        return 0
    except IntegrityError:
        db.rollback()
        print("Could not create administrator: username already exists.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
