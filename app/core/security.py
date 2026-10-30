import secrets

from fastapi import Header, HTTPException

from app.core.config import ADMIN_PASSWORD


def verify_admin_password(
    x_admin_password: str = Header(...),
):
    if not secrets.compare_digest(
        x_admin_password,
        ADMIN_PASSWORD,
    ):
        raise HTTPException(
            status_code=401,
            detail="رمز مدیریت نادرست است",
        )

    return True