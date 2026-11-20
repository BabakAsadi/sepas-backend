from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.features.course_enrollments.model import CourseEnrollment
from app.features.students.model import Student
from app.features.wallets.model import StudentWallet, WalletTransaction


WALLET_NOT_FOUND = "کیف پول دانش‌آموز پیدا نشد."


def _get_student_or_404(db: Session, student_id: int):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز پیدا نشد.")
    return student


def _get_or_create_wallet(db: Session, student_id: int):
    wallet = (
        db.query(StudentWallet)
        .filter(StudentWallet.student_id == student_id)
        .first()
    )
    if wallet:
        return wallet

    wallet = StudentWallet(student_id=student_id, balance=0)
    db.add(wallet)
    db.flush()
    return wallet


def get_wallet(db: Session, student_id: int):
    student = _get_student_or_404(db, student_id)
    wallet = (
        db.query(StudentWallet)
        .options(
            joinedload(StudentWallet.transactions).joinedload(
                WalletTransaction.enrollment
            )
        )
        .filter(StudentWallet.student_id == student_id)
        .first()
    )

    transactions = []
    if wallet:
        for item in wallet.transactions:
            enrollment = item.enrollment
            course = enrollment.course if enrollment else None
            transactions.append(
                {
                    "id": item.id,
                    "type": item.transaction_type,
                    "amount": item.amount,
                    "enrollment_id": item.enrollment_id,
                    "course_id": enrollment.course_id if enrollment else None,
                    "course_title": course.title if course else None,
                    "description": item.description,
                    "created_at": item.created_at.isoformat(),
                }
            )

    return {
        "student_id": student.id,
        "student_name": f"{student.first_name} {student.last_name}",
        "currency": "toman",
        "balance": wallet.balance if wallet else 0,
        "transactions": transactions,
    }


def top_up_wallet(db: Session, student_id: int, data):
    _get_student_or_404(db, student_id)
    wallet = _get_or_create_wallet(db, student_id)

    # Use an atomic increment so concurrent top-ups cannot overwrite each other.
    db.execute(
        update(StudentWallet)
        .where(StudentWallet.id == wallet.id)
        .values(balance=StudentWallet.balance + data.amount)
        .execution_options(synchronize_session=False)
    )
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="top_up",
        amount=data.amount,
        description=data.description.strip() if data.description else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    db.refresh(transaction)
    return wallet, transaction


def allocate_to_enrollment(db: Session, student_id: int, data):
    _get_student_or_404(db, student_id)
    enrollment = (
        db.query(CourseEnrollment)
        .options(joinedload(CourseEnrollment.course))
        .filter(
            CourseEnrollment.id == data.enrollment_id,
            CourseEnrollment.student_id == student_id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="عضویت انتخاب‌شده برای این دانش‌آموز پیدا نشد.",
        )

    wallet = (
        db.query(StudentWallet)
        .filter(StudentWallet.student_id == student_id)
        .first()
    )
    if not wallet:
        raise HTTPException(
            status_code=409,
            detail="کیف پول دانش‌آموز موجودی کافی ندارد.",
        )

    # Atomic conditional update prevents the wallet balance from becoming negative.
    result = db.execute(
        update(StudentWallet)
        .where(
            StudentWallet.id == wallet.id,
            StudentWallet.balance >= data.amount,
        )
        .values(balance=StudentWallet.balance - data.amount)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="موجودی کیف پول برای این تخصیص کافی نیست.",
        )

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="course_allocation",
        amount=data.amount,
        enrollment_id=enrollment.id,
        description=data.description.strip() if data.description else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    db.refresh(transaction)
    return wallet, transaction
