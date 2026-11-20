from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_SECURE,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.core.security import get_current_admin
from app.database.session import get_db
from app.features.auth.model import User
from app.features.auth.schemas import (
    LoginPayload,
    StudentUserCreate,
    TokenResponse,
    UserPasswordUpdate,
    UserStatusUpdate,
)
from app.features.auth.service import (
    authenticate_user,
    hash_password,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.features.students.model import Student

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginPayload,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است",
        )

    access_token, refresh_token = issue_token_pair(db, user)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ارسال نشده است",
        )
    access_token, new_refresh_token = rotate_refresh_token(db, refresh_token)
    set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    revoke_refresh_token(db, refresh_token)
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_student_user(
    payload: StudentUserCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد")

    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="این نام کاربری قبلاً ثبت شده است")
    if db.query(User).filter(User.student_id == student.id).first():
        raise HTTPException(status_code=409, detail="این دانش‌آموز قبلاً حساب کاربری دارد")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="student",
        student_id=student.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    users = db.query(User).order_by(User.id).all()
    return [user_to_dict(user) for user in users]


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    if user.role == "admin" and not payload.is_active:
        active_admins = db.query(User).filter(User.role == "admin", User.is_active.is_(True)).count()
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="امکان غیرفعال کردن آخرین مدیر وجود ندارد")
    user.is_active = payload.is_active
    if not payload.is_active:
        from app.features.auth.model import AuthSession
        from app.features.auth.service import utcnow
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        ).update({"revoked_at": utcnow()}, synchronize_session=False)
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.put("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_password(
    user_id: int,
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    from app.features.auth.model import AuthSession
    from app.features.auth.service import utcnow

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    user.password_hash = hash_password(payload.password)
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update({"revoked_at": utcnow()}, synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "student_id": user.student_id,
        "is_active": bool(user.is_active),
        "created_at": user.created_at,
    }
