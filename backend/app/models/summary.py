from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, DateTime, Numeric, ForeignKey, JSON,
    UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)

    # Nullable account_id means this row is an aggregate across all accounts
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    total_debit = Column(Numeric(12, 2), nullable=False, default=0)
    total_credit = Column(Numeric(12, 2), nullable=False, default=0)
    net = Column(Numeric(12, 2), nullable=False, default=0)  # credit - debit

    transaction_count = Column(Integer, nullable=False, default=0)
    category_breakdown = Column(JSON, nullable=True)  # {category_id: amount, ...}

    computed_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    account = relationship("Account")

    __table_args__ = (
        UniqueConstraint("account_id", "year", "month", name="uq_summary_account_year_month"),
    )
