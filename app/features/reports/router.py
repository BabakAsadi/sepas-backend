from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.reports import service
from app.shared.dependencies import get_db


router = APIRouter(prefix="/api/reports", tags=["Financial Reports"])


@router.get("/student-debts")
def get_student_debt_report(
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if as_of_date is not None and as_of_date > date.today():
        raise HTTPException(
            status_code=422,
            detail="تاریخ گزارش نمی‌تواند در آینده باشد.",
        )
    return service.get_student_debt_report(db, as_of_date)


@router.get("/courses/{course_id}")
def get_course_financial_report(
    course_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if as_of_date is not None and as_of_date > date.today():
        raise HTTPException(
            status_code=422,
            detail="تاریخ گزارش نمی‌تواند در آینده باشد.",
        )
    return service.get_course_financial_report(db, course_id, as_of_date)
