from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    bank_name: str
    account_type: str  # savings / current / credit_card
    account_number: Optional[str] = None  # last 4 digits
    account_holder: Optional[str] = None
    currency: str = "INR"


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_name: str
    account_type: str
    account_number: Optional[str]
    account_holder: Optional[str]
    currency: str
    is_active: bool
    created_at: datetime
