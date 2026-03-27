"""
Report/aggregation logic for charts and summaries.
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import func, extract, case
from sqlalchemy.orm import Session
from app.models import Transaction, Category


def get_monthly_summary(
    db: Session,
    year: int,
    month: int,
    account_id: int | None = None,
) -> dict:
    """
    Aggregate transactions for a month.
    Returns: {year, month, total_debit, total_credit, net, transaction_count,
              categories: [{category_id, category_name, amount, percentage, color, icon}]}
    Filter by account_id if provided.
    """
    query = db.query(Transaction).filter(
        extract("year", Transaction.transaction_date) == year,
        extract("month", Transaction.transaction_date) == month,
    )
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    transactions = query.all()

    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for txn in transactions:
        if txn.type == "debit":
            total_debit += txn.amount
        else:
            total_credit += txn.amount

    net = total_credit - total_debit

    # Category breakdown for debits
    category_query = (
        db.query(
            Transaction.category_id,
            Category.name.label("category_name"),
            Category.color,
            Category.icon,
            func.sum(Transaction.amount).label("total_amount"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.type == "debit",
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
    )
    if account_id is not None:
        category_query = category_query.filter(Transaction.account_id == account_id)

    category_rows = category_query.group_by(
        Transaction.category_id,
        Category.name,
        Category.color,
        Category.icon,
    ).all()

    categories = []
    investments_total = Decimal("0")
    for row in category_rows:
        amount = row.total_amount or Decimal("0")
        percentage = float(amount / total_debit * 100) if total_debit else 0.0
        categories.append({
            "category_id": row.category_id,
            "category_name": row.category_name or "Uncategorized",
            "amount": float(amount),
            "percentage": round(percentage, 2),
            "color": row.color,
            "icon": row.icon,
        })
        if row.category_name == "Investments":
            investments_total += amount

    # Sort by amount descending
    categories.sort(key=lambda x: x["amount"], reverse=True)

    expenses_total = total_debit - investments_total

    return {
        "year": year,
        "month": month,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "net": float(net),
        "transaction_count": len(transactions),
        "categories": categories,
        "investments_total": float(investments_total),
        "expenses_total": float(expenses_total),
    }


def get_yearly_trend(
    db: Session,
    year: int,
    account_id: int | None = None,
) -> list[dict]:
    """Return list of 12 monthly summaries for the given year."""
    return [
        get_monthly_summary(db, year, month, account_id)
        for month in range(1, 13)
    ]


def get_category_breakdown(
    db: Session,
    date_from: date,
    date_to: date,
    account_id: int | None = None,
) -> list[dict]:
    """
    Breakdown of DEBITS by category for a date range.
    Returns list of CategoryAmount dicts sorted by amount desc.
    Uncategorized transactions grouped under category_name='Uncategorized'.
    """
    query = (
        db.query(
            Transaction.category_id,
            Category.name.label("category_name"),
            Category.color,
            Category.icon,
            func.sum(Transaction.amount).label("total_amount"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.type == "debit",
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
    )

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    rows = query.group_by(
        Transaction.category_id,
        Category.name,
        Category.color,
        Category.icon,
    ).order_by(func.sum(Transaction.amount).desc()).all()

    # Compute grand total for percentage calculation
    grand_total = sum(row.total_amount or Decimal("0") for row in rows)

    result = []
    for row in rows:
        amount = row.total_amount or Decimal("0")
        percentage = float(amount / grand_total * 100) if grand_total else 0.0
        result.append({
            "category_id": row.category_id,
            "category_name": row.category_name or "Uncategorized",
            "amount": float(amount),
            "percentage": round(percentage, 2),
            "transaction_count": row.transaction_count,
            "color": row.color,
            "icon": row.icon,
        })

    return result


def get_pillars(
    db: Session,
    date_from: date,
    date_to: date,
    account_id: int | None = None,
) -> dict:
    """
    Aggregate transactions into 3 pillars for a date range:
      - income:      all credit transactions
      - investments: debit transactions in the 'Investments' category
      - expenses:    debit transactions NOT in the 'Investments' category

    Returns a dict with keys income, investments, expenses — each containing
    {total, count, transactions} plus expenses also has by_category.
    """
    base_query = db.query(Transaction).outerjoin(
        Category, Transaction.category_id == Category.id
    ).filter(
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    )
    if account_id is not None:
        base_query = base_query.filter(Transaction.account_id == account_id)

    all_txns = base_query.all()

    income_txns = []
    investment_txns = []
    expense_txns = []

    for txn in all_txns:
        cat_name = txn.category.name if txn.category else None
        if txn.type == "credit":
            income_txns.append(txn)
        elif txn.type == "debit":
            if cat_name == "Investments":
                investment_txns.append(txn)
            else:
                expense_txns.append(txn)

    def _txn_to_dict(t):
        return {
            "id": t.id,
            "transaction_date": str(t.transaction_date),
            "description": t.description,
            "amount": float(t.amount),
            "type": t.type,
            "category_id": t.category_id,
            "category_name": t.category.name if t.category else None,
            "account_id": t.account_id,
        }

    income_total = sum(t.amount for t in income_txns) or Decimal("0")
    investment_total = sum(t.amount for t in investment_txns) or Decimal("0")
    expense_total = sum(t.amount for t in expense_txns) or Decimal("0")

    # Build by_category for expenses (excluding Investments), sorted by amount desc
    expense_by_cat: dict[str, dict] = {}
    for txn in expense_txns:
        cat_name = (txn.category.name if txn.category else None) or "Uncategorized"
        cat_icon = txn.category.icon if txn.category else None
        cat_color = txn.category.color if txn.category else None
        if cat_name not in expense_by_cat:
            expense_by_cat[cat_name] = {
                "category_name": cat_name,
                "icon": cat_icon,
                "color": cat_color,
                "amount": Decimal("0"),
                "count": 0,
            }
        expense_by_cat[cat_name]["amount"] += txn.amount
        expense_by_cat[cat_name]["count"] += 1

    by_category = []
    for cat_data in sorted(expense_by_cat.values(), key=lambda x: x["amount"], reverse=True):
        amt = cat_data["amount"]
        percentage = float(amt / expense_total * 100) if expense_total else 0.0
        by_category.append({
            "category_name": cat_data["category_name"],
            "icon": cat_data["icon"],
            "color": cat_data["color"],
            "amount": float(amt),
            "percentage": round(percentage, 2),
        })

    return {
        "income": {
            "total": float(income_total),
            "count": len(income_txns),
            "transactions": [_txn_to_dict(t) for t in income_txns],
        },
        "investments": {
            "total": float(investment_total),
            "count": len(investment_txns),
            "transactions": [_txn_to_dict(t) for t in investment_txns],
        },
        "expenses": {
            "total": float(expense_total),
            "count": len(expense_txns),
            "transactions": [_txn_to_dict(t) for t in expense_txns],
            "by_category": by_category,
        },
    }


def get_pillars_trend(
    db: Session,
    year: int,
    account_id: int | None = None,
) -> list[dict]:
    """
    Return 12 monthly pillar totals for a given year.
    Each entry: {month, income, investments, expenses}
    """
    result = []
    for month in range(1, 13):
        query = db.query(Transaction).outerjoin(
            Category, Transaction.category_id == Category.id
        ).filter(
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
        if account_id is not None:
            query = query.filter(Transaction.account_id == account_id)

        txns = query.all()

        income = Decimal("0")
        investments = Decimal("0")
        expenses = Decimal("0")

        for txn in txns:
            cat_name = txn.category.name if txn.category else None
            if txn.type == "credit":
                income += txn.amount
            elif txn.type == "debit":
                if cat_name == "Investments":
                    investments += txn.amount
                else:
                    expenses += txn.amount

        result.append({
            "month": month,
            "income": float(income),
            "investments": float(investments),
            "expenses": float(expenses),
        })

    return result
