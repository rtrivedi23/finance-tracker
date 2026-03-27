from datetime import datetime, date
from sqlalchemy import Integer, String, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    period_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    parsed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    parse_status: Mapped[str] = mapped_column(String, default="success")  # success / partial / failed
    parse_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)

    account: Mapped["Account"] = relationship("Account", back_populates="statements")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="statement")
