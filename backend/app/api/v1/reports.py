"""
Reports API endpoints — monthly summaries, yearly trends, category breakdowns.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.report_service import (
    get_monthly_summary,
    get_yearly_trend,
    get_category_breakdown,
    get_pillars,
    get_pillars_trend,
)

router = APIRouter(prefix="", tags=["reports"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class CategorySummary(BaseModel):
    category_id: Optional[int]
    category_name: str
    amount: float
    percentage: float
    color: Optional[str]
    icon: Optional[str]


class MonthlySummaryResponse(BaseModel):
    year: int
    month: int
    total_debit: float
    total_credit: float
    net: float
    transaction_count: int
    categories: list[CategorySummary]
    investments_total: float
    expenses_total: float


class YearlyTrendResponse(BaseModel):
    year: int
    months: list[MonthlySummaryResponse]


class CategoryAmount(BaseModel):
    category_id: Optional[int]
    category_name: str
    amount: float
    percentage: float
    transaction_count: int
    color: Optional[str]
    icon: Optional[str]


class TransactionItem(BaseModel):
    id: int
    transaction_date: str
    description: Optional[str]
    amount: float
    type: str
    category_id: Optional[int]
    category_name: Optional[str]
    account_id: Optional[int]


class PillarDetail(BaseModel):
    total: float
    count: int
    transactions: list[TransactionItem]


class ExpenseCategoryBreakdown(BaseModel):
    category_name: str
    icon: Optional[str]
    color: Optional[str]
    amount: float
    percentage: float


class ExpensePillarDetail(BaseModel):
    total: float
    count: int
    transactions: list[TransactionItem]
    by_category: list[ExpenseCategoryBreakdown]


class PillarsResponse(BaseModel):
    income: PillarDetail
    investments: PillarDetail
    expenses: ExpensePillarDetail


class MonthlyPillarTrend(BaseModel):
    month: int
    income: float
    investments: float
    expenses: float


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
def monthly_summary(
    year: int = Query(..., description="4-digit year"),
    month: int = Query(..., ge=1, le=12, description="Month 1-12"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Aggregate transactions for a specific month."""
    data = get_monthly_summary(db, year, month, account_id)
    return MonthlySummaryResponse(
        year=data["year"],
        month=data["month"],
        total_debit=data["total_debit"],
        total_credit=data["total_credit"],
        net=data["net"],
        transaction_count=data["transaction_count"],
        categories=[CategorySummary(**cat) for cat in data["categories"]],
        investments_total=data["investments_total"],
        expenses_total=data["expenses_total"],
    )


@router.get("/yearly-trend", response_model=YearlyTrendResponse)
def yearly_trend(
    year: int = Query(..., description="4-digit year"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Return 12 monthly summaries for the given year."""
    monthly_data = get_yearly_trend(db, year, account_id)
    months = [
        MonthlySummaryResponse(
            year=m["year"],
            month=m["month"],
            total_debit=m["total_debit"],
            total_credit=m["total_credit"],
            net=m["net"],
            transaction_count=m["transaction_count"],
            categories=[CategorySummary(**cat) for cat in m["categories"]],
            investments_total=m["investments_total"],
            expenses_total=m["expenses_total"],
        )
        for m in monthly_data
    ]
    return YearlyTrendResponse(year=year, months=months)


@router.get("/category-breakdown", response_model=list[CategoryAmount])
def category_breakdown(
    date_from: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Breakdown of debits by category for a date range, sorted by amount desc."""
    data = get_category_breakdown(db, date_from, date_to, account_id)
    return [CategoryAmount(**row) for row in data]


@router.get("/pillars", response_model=PillarsResponse)
def pillars(
    date_from: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """3-pillar financial summary (Income, Investments, Expenses) for a date range."""
    data = get_pillars(db, date_from, date_to, account_id)
    return PillarsResponse(
        income=PillarDetail(
            total=data["income"]["total"],
            count=data["income"]["count"],
            transactions=[TransactionItem(**t) for t in data["income"]["transactions"]],
        ),
        investments=PillarDetail(
            total=data["investments"]["total"],
            count=data["investments"]["count"],
            transactions=[TransactionItem(**t) for t in data["investments"]["transactions"]],
        ),
        expenses=ExpensePillarDetail(
            total=data["expenses"]["total"],
            count=data["expenses"]["count"],
            transactions=[TransactionItem(**t) for t in data["expenses"]["transactions"]],
            by_category=[
                ExpenseCategoryBreakdown(**cat)
                for cat in data["expenses"]["by_category"]
            ],
        ),
    )


@router.get("/pillars-trend", response_model=list[MonthlyPillarTrend])
def pillars_trend(
    year: int = Query(..., description="4-digit year"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Monthly pillar totals for all 12 months of a given year (for charts)."""
    data = get_pillars_trend(db, year, account_id)
    return [MonthlyPillarTrend(**row) for row in data]
