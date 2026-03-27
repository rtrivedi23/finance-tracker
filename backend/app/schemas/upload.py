from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    statement_id: int
    account_id: int
    bank_name: str
    filename: str
    transaction_count: int
    parse_status: str               # 'success' / 'partial' / 'failed'
    parse_warnings: list[str] = []
    period_from: Optional[date] = None
    period_to: Optional[date] = None


class DuplicateFileResponse(BaseModel):
    message: str = "File already imported"
    statement_id: int
    imported_at: datetime
