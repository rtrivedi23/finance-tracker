from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    statement_id: int
    transaction_date: date
    value_date: Optional[date]
    description: str
    clean_description: Optional[str]
    amount: Decimal
    type: str  # 'debit' or 'credit'
    reference_number: Optional[str]
    balance_after: Optional[Decimal]
    category_id: Optional[int]
    is_manually_categorized: bool
    merchant_name: Optional[str]
    notes: Optional[str]
    raw_data: Optional[dict]
    created_at: datetime

    # Computed / joined field — not present on the ORM model directly
    category_name: Optional[str] = None


class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[str] = None          # 'debit' or 'credit'
    search: Optional[str] = None        # free-text search on description
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    page_size: int = 50


class CategoryUpdateRequest(BaseModel):
    category_id: int
