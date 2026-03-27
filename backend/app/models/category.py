from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)   # emoji
    color: Mapped[str | None] = mapped_column(String, nullable=True)  # hex color
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=100)

    rules: Mapped[list["CategorizationRule"]] = relationship("CategorizationRule", back_populates="category")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="category")


class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    pattern: Mapped[str] = mapped_column(String, nullable=False)
    match_field: Mapped[str] = mapped_column(String, default="description")
    match_type: Mapped[str] = mapped_column(String, default="contains")  # contains / regex / starts_with
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship("Category", back_populates="rules")
