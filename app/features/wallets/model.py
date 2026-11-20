from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class StudentWallet(Base):
    __tablename__ = "student_wallets"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_student_wallet_balance_nonnegative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    balance = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student = relationship("Student")
    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet",
        order_by="WalletTransaction.created_at.desc(), WalletTransaction.id.desc()",
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_wallet_transaction_amount_positive"),
        CheckConstraint(
            "transaction_type IN ('top_up', 'course_allocation')",
            name="ck_wallet_transaction_type",
        ),
        Index("ix_wallet_transaction_wallet_created", "wallet_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(
        Integer,
        ForeignKey("student_wallets.id"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(String(30), nullable=False)
    amount = Column(Integer, nullable=False)
    enrollment_id = Column(
        Integer,
        ForeignKey("course_enrollments.id"),
        nullable=True,
        index=True,
    )
    description = Column(String(500), nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    wallet = relationship("StudentWallet", back_populates="transactions")
    enrollment = relationship("CourseEnrollment")
