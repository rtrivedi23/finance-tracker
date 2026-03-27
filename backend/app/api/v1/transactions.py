"""
Transactions API endpoints.
"""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.database import get_db
from app.models import Transaction, Category

router = APIRouter(prefix="", tags=["transactions"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class CategoryInfo(BaseModel):
    id: Optional[int]
    name: Optional[str]
    icon: Optional[str]
    color: Optional[str]


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    statement_id: Optional[int]
    transaction_date: date
    value_date: Optional[date]
    description: str
    clean_description: Optional[str]
    amount: float
    type: str
    reference_number: Optional[str]
    balance_after: Optional[float]
    category_id: Optional[int]
    category_name: Optional[str]
    category_icon: Optional[str]
    category_color: Optional[str]
    is_manually_categorized: bool
    merchant_name: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class PaginatedTransactions(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


class CategoryUpdateRequest(BaseModel):
    category_id: Optional[int]


class TransactionStats(BaseModel):
    total_debit: float
    total_credit: float
    net: float
    count: int


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=TransactionStats)
def get_transaction_stats(
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Basic stats: total_debit, total_credit, net, count for current month."""
    now = datetime.utcnow()
    query = db.query(Transaction).filter(
        extract("year", Transaction.transaction_date) == now.year,
        extract("month", Transaction.transaction_date) == now.month,
    )
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    transactions = query.all()

    total_debit = sum(t.amount for t in transactions if t.type == "debit")
    total_credit = sum(t.amount for t in transactions if t.type == "credit")
    return TransactionStats(
        total_debit=float(total_debit),
        total_credit=float(total_credit),
        net=float(total_credit - total_debit),
        count=len(transactions),
    )


@router.get("/", response_model=PaginatedTransactions)
def list_transactions(
    account_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None, description="debit or credit"),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    List transactions with optional filters.
    Joins with categories to include category_name, icon, color.
    """
    query = (
        db.query(
            Transaction,
            Category.name.label("category_name"),
            Category.icon.label("category_icon"),
            Category.color.label("category_color"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
    )

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if type is not None:
        query = query.filter(Transaction.type == type)
    if search:
        search_term = f"%{search.upper()}%"
        query = query.filter(
            Transaction.description.ilike(search_term)
            | Transaction.merchant_name.ilike(search_term)
        )
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)

    total = query.count()

    offset = (page - 1) * page_size
    rows = (
        query.order_by(Transaction.transaction_date.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for txn, cat_name, cat_icon, cat_color in rows:
        items.append(
            TransactionResponse(
                id=txn.id,
                account_id=txn.account_id,
                statement_id=txn.statement_id,
                transaction_date=txn.transaction_date,
                value_date=txn.value_date,
                description=txn.description,
                clean_description=txn.clean_description,
                amount=float(txn.amount),
                type=txn.type,
                reference_number=txn.reference_number,
                balance_after=float(txn.balance_after) if txn.balance_after is not None else None,
                category_id=txn.category_id,
                category_name=cat_name,
                category_icon=cat_icon,
                category_color=cat_color,
                is_manually_categorized=txn.is_manually_categorized,
                merchant_name=txn.merchant_name,
                notes=txn.notes,
            )
        )

    return PaginatedTransactions(items=items, total=total, page=page, page_size=page_size)


@router.patch("/{transaction_id}/category", response_model=TransactionResponse)
def update_transaction_category(
    transaction_id: int,
    payload: CategoryUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update a transaction's category and mark it as manually categorized."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn.category_id = payload.category_id
    txn.is_manually_categorized = True
    db.commit()
    db.refresh(txn)

    # Fetch category info for response
    category = db.query(Category).filter(Category.id == txn.category_id).first() if txn.category_id else None

    return TransactionResponse(
        id=txn.id,
        account_id=txn.account_id,
        statement_id=txn.statement_id,
        transaction_date=txn.transaction_date,
        value_date=txn.value_date,
        description=txn.description,
        clean_description=txn.clean_description,
        amount=float(txn.amount),
        type=txn.type,
        reference_number=txn.reference_number,
        balance_after=float(txn.balance_after) if txn.balance_after is not None else None,
        category_id=txn.category_id,
        category_name=category.name if category else None,
        category_icon=category.icon if category else None,
        category_color=category.color if category else None,
        is_manually_categorized=txn.is_manually_categorized,
        merchant_name=txn.merchant_name,
        notes=txn.notes,
    )
