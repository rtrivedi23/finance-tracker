"""
Accounts API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Account

router = APIRouter(prefix="", tags=["accounts"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class AccountResponse(BaseModel):
    id: int
    bank_name: str
    account_type: str
    account_number: Optional[str]
    account_holder: Optional[str]
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    bank_name: str
    account_type: str = "savings"
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    currency: str = "INR"


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[AccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    """List all active accounts."""
    return db.query(Account).filter(Account.is_active == True).all()


@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    account = Account(
        bank_name=payload.bank_name,
        account_type=payload.account_type,
        account_number=payload.account_number,
        account_holder=payload.account_holder,
        currency=payload.currency,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get a single account by ID."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """Soft-delete an account by setting is_active=False."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    db.commit()
