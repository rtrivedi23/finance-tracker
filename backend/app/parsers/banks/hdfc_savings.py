"""HDFC Bank savings-account statement parser.

Supports both CSV and PDF formats.

CSV column layout (example):
    Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt.(Dr.) | Deposit Amt.(Cr.) | Closing Balance

PDF layout: same columns, extracted via pdfplumber.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.parsers.base import BaseParser, ParseResult, RawTransaction
from app.parsers.csv_utils import read_csv_flexible, parse_inr_amount, find_header_row_in_file
from app.parsers.pdf_utils import extract_text_pdfplumber, extract_tables_pdfplumber, clean_cell


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> Optional[date]:
    """Try common Indian date formats: DD/MM/YY, DD/MM/YYYY, YYYY-MM-DD."""
    raw = str(raw).strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y"):
        try:
            return date.strptime(raw, fmt) if hasattr(date, "strptime") else \
                   __import__("datetime").datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _safe_date(raw: str) -> Optional[date]:
    try:
        return _parse_date(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Column name constants (HDFC)
# ---------------------------------------------------------------------------

_COL_DATE = "Date"
_COL_NARRATION = "Narration"
_COL_REF = "Chq./Ref.No."
_COL_VALUE_DT = "Value Dt"
_COL_WITHDRAWAL = "Withdrawal Amt.(Dr.)"
_COL_DEPOSIT = "Deposit Amt.(Cr.)"
_COL_BALANCE = "Closing Balance"

_DETECT_KEYWORDS_CSV = {"Narration", "Withdrawal Amt", "Deposit Amt"}
_DETECT_KEYWORDS_PDF = {"HDFC Bank", "Statement of Account"}


class HDFCSavingsParser(BaseParser):
    BANK_NAME = "HDFC"

    # ------------------------------------------------------------------
    # detect()
    # ------------------------------------------------------------------

    @classmethod
    def detect(cls, file_path: Path) -> bool:
        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return cls._detect_csv(file_path)
        elif suffix == ".pdf":
            return cls._detect_pdf(file_path)
        return False

    @classmethod
    def _detect_csv(cls, file_path: Path) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(3000)
            return all(kw.lower() in content.lower() for kw in _DETECT_KEYWORDS_CSV)
        except Exception:
            return False

    @classmethod
    def _detect_pdf(cls, file_path: Path) -> bool:
        try:
            first_page_text = extract_text_pdfplumber(file_path)[:2000]
            return all(kw in first_page_text for kw in _DETECT_KEYWORDS_PDF)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # parse()
    # ------------------------------------------------------------------

    def parse(self, file_path: Path) -> ParseResult:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self._parse_pdf(file_path)
        return self._parse_csv(file_path)

    # ------------------------------------------------------------------
    # CSV parser
    # ------------------------------------------------------------------

    def _parse_csv(self, file_path: Path) -> ParseResult:
        warnings: list[str] = []

        # Find header row by scanning file line-by-line
        header_row_idx = find_header_row_in_file(file_path, ["Narration", "Withdrawal"])
        if header_row_idx < 0:
            warnings.append("Could not locate HDFC CSV header row; defaulting to row 0.")
            header_row_idx = 0

        # Re-read using discovered header row
        df = read_csv_flexible(file_path, skip_rows=header_row_idx, header=0)
        df.columns = [str(c).strip() for c in df.columns]

        return self._build_parse_result(df, warnings)

    # ------------------------------------------------------------------
    # PDF parser
    # ------------------------------------------------------------------

    def _parse_pdf(self, file_path: Path) -> ParseResult:
        warnings: list[str] = []
        tables = extract_tables_pdfplumber(file_path)

        rows: list[list[str]] = []
        header: Optional[list[str]] = None

        for table in tables:
            for row in table:
                row_str = " ".join(row)
                if header is None and "Narration" in row_str and "Withdrawal" in row_str:
                    header = [c.strip() for c in row]
                elif header is not None:
                    rows.append(row)

        if header is None:
            return ParseResult(
                transactions=[],
                period_from=None,
                period_to=None,
                account_number=None,
                bank_name=self.BANK_NAME,
                warnings=["Could not find transaction table headers in HDFC PDF."],
            )

        df = pd.DataFrame(rows, columns=header)
        return self._build_parse_result(df, warnings)

    # ------------------------------------------------------------------
    # Shared builder
    # ------------------------------------------------------------------

    def _build_parse_result(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> ParseResult:
        transactions: list[RawTransaction] = []

        # Normalise column names — strip whitespace
        col_map = {c: c.strip() for c in df.columns}
        df = df.rename(columns=col_map)

        # Identify actual column names (HDFC may vary slightly)
        date_col = self._find_col(df, [_COL_DATE, "Txn Date", "Transaction Date"])
        narr_col = self._find_col(df, [_COL_NARRATION, "Description"])
        ref_col = self._find_col(df, [_COL_REF, "Ref No", "Reference"])
        vdate_col = self._find_col(df, [_COL_VALUE_DT, "Value Date"])
        wd_col = self._find_col(df, [_COL_WITHDRAWAL, "Withdrawal", "Debit"])
        dep_col = self._find_col(df, [_COL_DEPOSIT, "Deposit", "Credit"])
        bal_col = self._find_col(df, [_COL_BALANCE, "Balance"])

        for row_idx, row in df.iterrows():
            raw_date = str(row.get(date_col, "")).strip() if date_col else ""
            if not raw_date or raw_date.lower() in ("date", "nan", ""):
                continue  # skip header-repeat or empty rows

            txn_date = _safe_date(raw_date)
            if txn_date is None:
                warnings.append(f"Row {row_idx}: could not parse date '{raw_date}'; skipping.")
                continue

            description = str(row.get(narr_col, "")).strip() if narr_col else ""
            reference = str(row.get(ref_col, "")).strip() if ref_col else None
            if reference in ("nan", ""):
                reference = None

            value_date: Optional[date] = None
            if vdate_col:
                value_date = _safe_date(str(row.get(vdate_col, "")).strip())

            balance: Optional[Decimal] = None
            if bal_col:
                try:
                    balance = parse_inr_amount(row.get(bal_col))
                except Exception:
                    balance = None

            # Determine amount and direction
            withdrawal_raw = str(row.get(wd_col, "")).strip() if wd_col else ""
            deposit_raw = str(row.get(dep_col, "")).strip() if dep_col else ""

            withdrawal_amt: Optional[Decimal] = None
            deposit_amt: Optional[Decimal] = None

            if withdrawal_raw and withdrawal_raw not in ("nan", "", "0", "0.00"):
                try:
                    withdrawal_amt = parse_inr_amount(withdrawal_raw)
                except Exception as e:
                    warnings.append(f"Row {row_idx}: withdrawal parse error: {e}")

            if deposit_raw and deposit_raw not in ("nan", "", "0", "0.00"):
                try:
                    deposit_amt = parse_inr_amount(deposit_raw)
                except Exception as e:
                    warnings.append(f"Row {row_idx}: deposit parse error: {e}")

            if withdrawal_amt and withdrawal_amt > 0:
                txn_type = "debit"
                amount = withdrawal_amt
            elif deposit_amt and deposit_amt > 0:
                txn_type = "credit"
                amount = deposit_amt
            else:
                warnings.append(
                    f"Row {row_idx}: no valid debit or credit amount found; skipping."
                )
                continue

            transactions.append(
                RawTransaction(
                    date=txn_date,
                    description=description,
                    amount=amount,
                    type=txn_type,
                    value_date=value_date,
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

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        """Return the first column name from *candidates* that exists in *df*."""
        for c in candidates:
            if c in df.columns:
                return c
            # Try case-insensitive match
            for col in df.columns:
                if col.lower().strip() == c.lower().strip():
                    return col
        return None
