from datetime import date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    period_type = Column(String(10), nullable=False)  # 'monthly' or 'yearly'

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    notes = Column(String, nullable=True)

    # Relationships
    category = relationship("Category")
