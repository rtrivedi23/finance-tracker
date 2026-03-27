"""
Orchestrates the full import pipeline: upload -> detect -> parse -> dedup -> categorize -> save
"""

import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.parsers.detector import detect_parser
from app.categorizer.engine import CategorizationEngine
from app.models import Account, BankStatement, Transaction


def compute_file_hash(file_path: Path) -> str:
    """SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def import_statement(db: Session, file_path: Path, filename: str) -> dict:
    """
    Full import pipeline:
    1. Compute file hash
    2. Check if hash exists in bank_statements — if yes, return duplicate info
    3. detect_parser(file_path) — raise ValueError if no parser found
    4. parser.parse(file_path) -> ParseResult
    5. Find or create Account matching (bank_name, account_number)
       - account_type defaults to 'savings' (user can change later)
    6. Create BankStatement record
    7. Convert RawTransaction list to Transaction ORM objects (not yet committed)
    8. Run CategorizationEngine.categorize_batch() on transactions
    9. bulk insert transactions, update statement.transaction_count
    10. db.commit()
    11. Return dict with: statement_id, account_id, bank_name, filename,
        transaction_count, parse_status, parse_warnings, period_from, period_to
    """
    # Step 1: Compute file hash
    file_hash = compute_file_hash(file_path)

    # Step 2: Check for duplicate
    existing_statement = (
        db.query(BankStatement)
        .filter(BankStatement.file_hash == file_hash)
        .first()
    )
    if existing_statement:
        # If the previous import had 0 transactions (failed parse), delete it and re-import
        if existing_statement.transaction_count == 0:
            db.delete(existing_statement)
            db.commit()
        else:
            return {
                "duplicate": True,
                "message": f"This file has already been imported (statement id: {existing_statement.id})",
                "statement_id": existing_statement.id,
                "account_id": existing_statement.account_id,
                "filename": existing_statement.filename,
                "parse_warnings": [],
                "transaction_count": existing_statement.transaction_count,
                "bank_name": "",
                "parse_status": "duplicate",
                "period_from": None,
                "period_to": None,
            }

    # Step 3: Detect parser
    parser = detect_parser(file_path)
    if parser is None:
        raise ValueError(f"No parser found for file: {filename}")

    # Step 4: Parse the file
    parse_result = parser.parse(file_path)

    # Step 5: Find or create Account
    bank_name = parse_result.bank_name
    account_number = parse_result.account_number

    account = None
    if account_number:
        # Match on bank_name + last 4 digits of account_number
        last_four = account_number[-4:]
        account = (
            db.query(Account)
            .filter(
                Account.bank_name == bank_name,
                Account.account_number.like(f"%{last_four}"),
                Account.is_active == True,
            )
            .first()
        )
    else:
        # Match on bank_name only
        account = (
            db.query(Account)
            .filter(Account.bank_name == bank_name, Account.is_active == True)
            .first()
        )

    if account is None:
        account = Account(
            bank_name=bank_name,
            account_number=account_number,
            account_type="savings",
            account_holder=None,
            currency="INR",
            is_active=True,
        )
        db.add(account)
        db.flush()

    # Step 6: Create BankStatement record
    statement = BankStatement(
        account_id=account.id,
        filename=filename,
        file_hash=file_hash,
        file_path=str(file_path),
        period_from=parse_result.period_from,
        period_to=parse_result.period_to,
        parsed_at=datetime.utcnow(),
        parse_status="pending",
        parse_errors=None,
        transaction_count=0,
    )
    db.add(statement)
    db.flush()

    # Step 7: Convert RawTransaction list to Transaction ORM objects
    transactions: list[Transaction] = []
    for raw in parse_result.transactions:
        txn = Transaction(
            account_id=account.id,
            statement_id=statement.id,
            transaction_date=raw.date,
            value_date=raw.value_date,
            description=raw.description,
            clean_description=None,
            amount=raw.amount,
            type=raw.type,
            reference_number=raw.reference,
            balance_after=raw.balance,
            category_id=None,
            is_manually_categorized=False,
            merchant_name=None,
            notes=None,
            raw_data=raw.raw_row,
        )
        transactions.append(txn)

    # Step 8: Run categorization
    engine = CategorizationEngine(db)
    engine.categorize_batch(transactions)

    # Step 9: Bulk insert transactions and update statement count
    db.add_all(transactions)
    statement.transaction_count = len(transactions)
    statement.parse_status = "success"
    if parse_result.warnings:
        statement.parse_errors = {"warnings": parse_result.warnings}

    # Step 10: Commit
    db.commit()

    # Step 11: Return summary dict
    return {
        "duplicate": False,
        "statement_id": statement.id,
        "account_id": account.id,
        "bank_name": bank_name,
        "filename": filename,
        "transaction_count": len(transactions),
        "parse_status": statement.parse_status,
        "parse_warnings": parse_result.warnings,
        "period_from": parse_result.period_from,
        "period_to": parse_result.period_to,
    }
