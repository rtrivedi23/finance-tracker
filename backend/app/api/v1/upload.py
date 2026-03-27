"""
File upload endpoint — triggers the full import pipeline.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.import_service import import_statement

router = APIRouter(prefix="", tags=["upload"])

# Directory where uploaded files are stored
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "uploads"))


# ── Schemas ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    duplicate: bool = False
    statement_id: int
    account_id: int
    bank_name: str
    filename: str
    transaction_count: int
    parse_status: str
    parse_warnings: list[str]
    period_from: Optional[str]
    period_to: Optional[str]


class DuplicateFileResponse(BaseModel):
    duplicate: bool = True
    message: str
    statement_id: int
    account_id: int
    filename: str


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/", status_code=200)
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a bank statement file upload (PDF or CSV).
    Saves with a timestamp prefix to avoid collisions.
    Triggers the full import pipeline.
    Returns UploadResponse or DuplicateFileResponse (HTTP 200).
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Build timestamped filename to prevent collisions on open files
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOADS_DIR / safe_filename

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")

    try:
        result = import_statement(db, file_path, file.filename)
    except ValueError as exc:
        # Clean up the saved file if parsing fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")

    if result.get("duplicate"):
        return DuplicateFileResponse(
            duplicate=True,
            message=result["message"],
            statement_id=result["statement_id"],
            account_id=result["account_id"],
            filename=result["filename"],
        )

    return UploadResponse(
        duplicate=False,
        statement_id=result["statement_id"],
        account_id=result["account_id"],
        bank_name=result["bank_name"],
        filename=result["filename"],
        transaction_count=result["transaction_count"],
        parse_status=result["parse_status"],
        parse_warnings=result.get("parse_warnings", []),
        period_from=str(result["period_from"]) if result["period_from"] else None,
        period_to=str(result["period_to"]) if result["period_to"] else None,
    )
