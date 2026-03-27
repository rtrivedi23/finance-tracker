from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class CategoryAmount(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    amount: Decimal
    percentage: float
    color: Optional[str] = None
    icon: Optional[str] = None


class MonthlySummaryResponse(BaseModel):
    year: int
    month: int
    total_debit: Decimal
    total_credit: Decimal
    net: Decimal
    transaction_count: int
    categories: list[CategoryAmount] = []


class YearlyTrendResponse(BaseModel):
    months: list[MonthlySummaryResponse]


class ReportRequest(BaseModel):
    account_id: Optional[int] = None
    date_from: date
    date_to: date
