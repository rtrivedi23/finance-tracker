"""Generic CSV / Excel parser used as a last-resort fallback.

Attempts to intelligently map column names to standard transaction fields
by pattern-matching against common variants found in Indian bank statements.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.parsers.base import BaseParser, ParseResult, RawTransaction
from app.parsers.csv_utils import read_csv_flexible, read_excel_flexible, parse_inr_amount


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> Optional[date]:
    from datetime import datetime as dt

    raw = str(raw).strip()
    for fmt in (
        "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d",
        "%d-%m-%Y", "%d-%b-%Y", "%b %d, %Y",
        "%m/%d/%Y",
    ):
        try:
            return dt.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _safe_date(raw: str) -> Optional[date]:
    try:
        return _parse_date(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Column-mapping heuristics
# ---------------------------------------------------------------------------

_DATE_HINTS = [
    "transaction date", "txn date", "date", "value date", "posting date",
    "trans date",
]
_DESC_HINTS = [
    "description", "narration", "transaction remarks", "remarks", "details",
    "particulars", "trans description", "memo",
]
_DEBIT_HINTS = [
    "withdrawal", "debit", "dr", "withdrawal amt", "debit amount",
    "withdrawal amount (inr)", "debit amt",
]
_CREDIT_HINTS = [
    "deposit", "credit", "cr", "deposit amt", "credit amount",
    "deposit amount (inr)", "credit amt",
]
_AMOUNT_HINTS = ["amount", "transaction amount", "txn amount"]
_BALANCE_HINTS = ["balance", "closing balance", "balance (inr)", "running balance"]
_REF_HINTS = ["reference", "chq no", "cheque number", "ref no", "utr", "transaction id"]


def _match_col(df: pd.DataFrame, hints: list[str]) -> Optional[str]:
    """Return the first column whose normalised name matches any hint."""
    norm = {col: col.lower().strip() for col in df.columns}
    for hint in hints:
        for col, col_lower in norm.items():
            if hint in col_lower or col_lower in hint:
                return col
    return None


# ---------------------------------------------------------------------------
# Parser class
# ---------------------------------------------------------------------------

class GenericCSVParser(BaseParser):
    BANK_NAME = "Unknown"

    @classmethod
    def detect(cls, file_path: Path) -> bool:
        """Accept any CSV or Excel file as a last-resort fallback."""
        return file_path.suffix.lower() in (".csv", ".xlsx", ".xls")

    def parse(self, file_path: Path) -> ParseResult:
        warnings: list[str] = []
        suffix = file_path.suffix.lower()

        # ------------------------------------------------------------------
        # Load data
        # ------------------------------------------------------------------
        try:
            if suffix in (".xlsx", ".xls"):
                df = read_excel_flexible(file_path)
            else:
                df = read_csv_flexible(file_path)
        except Exception as exc:
            return ParseResult(
                transactions=[],
                period_from=None,
                period_to=None,
                account_number=None,
                bank_name=self.BANK_NAME,
                warnings=[f"Could not read file: {exc}"],
            )

        df.columns = [str(c).strip() for c in df.columns]

        # ------------------------------------------------------------------
        # Discover columns
        # ------------------------------------------------------------------
        date_col = _match_col(df, _DATE_HINTS)
        desc_col = _match_col(df, _DESC_HINTS)
        debit_col = _match_col(df, _DEBIT_HINTS)
        credit_col = _match_col(df, _CREDIT_HINTS)
        amount_col = _match_col(df, _AMOUNT_HINTS) if not (debit_col or credit_col) else None
        balance_col = _match_col(df, _BALANCE_HINTS)
        ref_col = _match_col(df, _REF_HINTS)

        if date_col is None:
            warnings.append(
                "No date column detected; cannot parse transactions from this file."
            )
            return ParseResult(
                transactions=[],
                period_from=None,
                period_to=None,
                account_number=None,
                bank_name=self.BANK_NAME,
                warnings=warnings,
            )

        if desc_col is None:
            warnings.append("No description/narration column detected; descriptions will be empty.")

        if not (debit_col or credit_col or amount_col):
            warnings.append("No amount column detected; cannot parse transaction amounts.")
            return ParseResult(
                transactions=[],
                period_from=None,
                period_to=None,
                account_number=None,
                bank_name=self.BANK_NAME,
                warnings=warnings,
            )

        # Emit informational warnings for ambiguous situations
        if amount_col and not (debit_col or credit_col):
            warnings.append(
                "Using generic 'amount' column — all transactions will be treated as debits "
                "unless the value is negative (which will be treated as credit)."
            )

        # ------------------------------------------------------------------
        # Build transactions
        # ------------------------------------------------------------------
        transactions: list[RawTransaction] = []

        for row_idx, row in df.iterrows():
            raw_date = str(row.get(date_col, "")).strip()
            if not raw_date or raw_date.lower() in ("nan", "date", ""):
                continue

            txn_date = _safe_date(raw_date)
            if txn_date is None:
                warnings.append(
                    f"Row {row_idx}: could not parse date '{raw_date}'; skipping."
                )
                continue

            description = str(row.get(desc_col, "")).strip() if desc_col else ""

            reference = str(row.get(ref_col, "")).strip() if ref_col else None
            if reference in ("nan", ""):
                reference = None

            balance: Optional[Decimal] = None
            if balance_col:
                try:
                    balance = parse_inr_amount(row.get(balance_col))
                except Exception:
                    balance = None

            # -- Amount resolution --
            if debit_col or credit_col:
                wd_raw = str(row.get(debit_col, "")).strip() if debit_col else ""
                dep_raw = str(row.get(credit_col, "")).strip() if credit_col else ""

                withdrawal_amt: Optional[Decimal] = None
                deposit_amt: Optional[Decimal] = None

                if wd_raw and wd_raw not in ("nan", "", "0", "0.00"):
                    try:
                        withdrawal_amt = parse_inr_amount(wd_raw)
                    except Exception as e:
                        warnings.append(f"Row {row_idx}: debit parse error: {e}")

                if dep_raw and dep_raw not in ("nan", "", "0", "0.00"):
                    try:
                        deposit_amt = parse_inr_amount(dep_raw)
                    except Exception as e:
                        warnings.append(f"Row {row_idx}: credit parse error: {e}")

                if withdrawal_amt and withdrawal_amt > 0:
                    txn_type: str = "debit"
                    amount: Decimal = withdrawal_amt
                elif deposit_amt and deposit_amt > 0:
                    txn_type = "credit"
                    amount = deposit_amt
                else:
                    warnings.append(
                        f"Row {row_idx}: no valid debit or credit amount; skipping."
                    )
                    continue
            else:
                # Generic single-amount column
                raw_amt = str(row.get(amount_col, "")).strip()  # type: ignore[arg-type]
                if not raw_amt or raw_amt.lower() in ("nan", ""):
                    continue
                try:
                    parsed_amt = parse_inr_amount(raw_amt)
                except Exception as e:
                    warnings.append(f"Row {row_idx}: amount parse error: {e}; skipping.")
                    continue

                if parsed_amt < 0:
                    txn_type = "credit"
                    amount = abs(parsed_amt)
                else:
                    txn_type = "debit"
                    amount = parsed_amt

            if amount == 0:
                warnings.append(f"Row {row_idx}: zero-amount transaction; skipping.")
                continue

            transactions.append(
                RawTransaction(
                    date=txn_date,
                    description=description,
                    amount=amount,
                    type=txn_type,
                    value_date=None,
                    reference=reference,
                    balance=balance,
                    raw_row=row.to_dict() if hasattr(row, "to_dict") else {},
                )
            )

        dates = [t.date for t in transactions]
        return ParseResult(
            transactions=transactions,
            period_from=min(dates) if dates else None,
            period_to=max(dates) if dates else None,
            account_number=None,
            bank_name=self.BANK_NAME,
            warnings=warnings,
        )
