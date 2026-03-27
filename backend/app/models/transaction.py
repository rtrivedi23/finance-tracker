from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean,
    Numeric, ForeignKey, JSON, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    statement_id = Column(Integer, ForeignKey("bank_statements.id"), nullable=False, index=True)

    transaction_date = Column(Date, nullable=False, index=True)
    value_date = Column(Date, nullable=True)

    description = Column(String, nullable=False)
    clean_description = Column(String, nullable=True)

    # Amount is always stored as a positive value; type indicates direction
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # 'debit' or 'credit'

    reference_number = Column(String, nullable=True)
    balance_after = Column(Numeric(12, 2), nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    is_manually_categorized = Column(Boolean, default=False, nullable=False)

    merchant_name = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    account = relationship("Account", back_populates="transactions")
    statement = relationship("BankStatement", back_populates="transactions")
    category = relationship("Category")
