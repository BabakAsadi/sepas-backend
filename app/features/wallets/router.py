from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.wallets import service
from app.features.wallets.schemas import (
    WalletAllocationPayload,
    WalletTopUpPayload,
)
from app.shared.dependencies import get_db


router = APIRouter(prefix="/api/wallets", tags=["Student Wallets"])


def transaction_to_dict(transaction, wallet):
    enrollment = transaction.enrollment
    course = enrollment.course if enrollment else None
    return {
        "id": transaction.id,
        "type": transaction.transaction_type,
        "amount": transaction.amount,
        "enrollment_id": transaction.enrollment_id,
        "course_id": enrollment.course_id if enrollment else None,
        "course_title": course.title if course else None,
        "description": transaction.description,
        "created_at": transaction.created_at.isoformat(),
        "wallet_balance": wallet.balance,
        "currency": "toman",
    }


@router.get("/{student_id}")
def get_wallet(
    student_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_wallet(db, student_id)


@router.post("/{student_id}/top-ups", status_code=201)
def top_up_wallet(
    student_id: Annotated[int, Path(gt=0)],
    data: WalletTopUpPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    wallet, transaction = service.top_up_wallet(db, student_id, data)
    return transaction_to_dict(transaction, wallet)


@router.post("/{student_id}/allocations", status_code=201)
def allocate_to_course_enrollment(
    student_id: Annotated[int, Path(gt=0)],
    data: WalletAllocationPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    wallet, transaction = service.allocate_to_enrollment(db, student_id, data)
    return transaction_to_dict(transaction, wallet)
