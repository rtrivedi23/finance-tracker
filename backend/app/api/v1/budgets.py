"""
Budgets API endpoints.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import Budget, Category, Transaction

router = APIRouter(prefix="", tags=["budgets"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class BudgetResponse(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str]
    category_icon: Optional[str]
    category_color: Optional[str]
    amount: float
    period_type: str
    start_date: Optional[str]
    end_date: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    category_id: int
    amount: float
    period_type: str = "monthly"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class BudgetVsActual(BaseModel):
    category_id: int
    category_name: str
    category_icon: Optional[str]
    category_color: Optional[str]
    budgeted: float
    actual: float
    remaining: float
    percentage_used: float


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/vs-actual", response_model=list[BudgetVsActual])
def budget_vs_actual(
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Current month budget vs actual spending per category.
    Only categories that have budgets are included.
    """
    now = datetime.utcnow()
    year = now.year
    month = now.month

    budgets = (
        db.query(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .all()
    )

    if not budgets:
        return []

    # Collect budgeted category IDs
    budget_category_ids = [b.category_id for b, _ in budgets]

    # Query actual spending for those categories this month
    actuals_query = (
        db.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.type == "debit",
            Transaction.category_id.in_(budget_category_ids),
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
    )
    if account_id is not None:
        actuals_query = actuals_query.filter(Transaction.account_id == account_id)

    actuals = actuals_query.group_by(Transaction.category_id).all()
    actuals_map = {row.category_id: float(row.total or 0) for row in actuals}

    result = []
    for budget, category in budgets:
        budgeted = float(budget.amount)
        actual = actuals_map.get(budget.category_id, 0.0)
        remaining = budgeted - actual
        percentage_used = round((actual / budgeted * 100) if budgeted > 0 else 0.0, 2)

        result.append(
            BudgetVsActual(
                category_id=budget.category_id,
                category_name=category.name,
                category_icon=category.icon,
                category_color=category.color,
                budgeted=budgeted,
                actual=actual,
                remaining=remaining,
                percentage_used=percentage_used,
            )
        )

    return result


@router.get("/", response_model=list[BudgetResponse])
def list_budgets(db: Session = Depends(get_db)):
    """List all budgets with associated category info."""
    rows = (
        db.query(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .all()
    )

    result = []
    for budget, category in rows:
        result.append(
            BudgetResponse(
                id=budget.id,
                category_id=budget.category_id,
                category_name=category.name,
                category_icon=category.icon,
                category_color=category.color,
                amount=float(budget.amount),
                period_type=budget.period_type,
                start_date=str(budget.start_date) if budget.start_date else None,
                end_date=str(budget.end_date) if budget.end_date else None,
                notes=budget.notes,
            )
        )
    return result


@router.post("/", response_model=BudgetResponse, status_code=201)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db)):
    """Create a new budget for a category."""
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    budget = Budget(
        category_id=payload.category_id,
        amount=Decimal(str(payload.amount)),
        period_type=payload.period_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    return BudgetResponse(
        id=budget.id,
        category_id=budget.category_id,
        category_name=category.name,
        category_icon=category.icon,
        category_color=category.color,
        amount=float(budget.amount),
        period_type=budget.period_type,
        start_date=str(budget.start_date) if budget.start_date else None,
        end_date=str(budget.end_date) if budget.end_date else None,
        notes=budget.notes,
    )


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget by ID."""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
