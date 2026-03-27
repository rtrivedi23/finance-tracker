"""ICICI Bank savings-account statement parser.

Supports both CSV and PDF formats.

CSV column layout (example):
    S No. | Value Date | Transaction Date | Cheque Number | Transaction Remarks
          | Withdrawal Amount (INR ) | Deposit Amount (INR ) | Balance (INR )

Note: ICICI column names sometimes contain trailing spaces, so all comparisons
are done after stripping.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.parsers.base import BaseParser, ParseResult, RawTransaction
from app.parsers.csv_utils import read_csv_flexible, parse_inr_amount, find_header_row_in_file
from app.parsers.pdf_utils import extract_text_pdfplumber, extract_tables_pdfplumber


# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: str) -> Optional[date]:
    """Try common Indian date formats: DD/MM/YYYY, DD/MM/YY, YYYY-MM-DD."""
    from datetime import datetime as dt

    raw = str(raw).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y"):
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
# Column keyword constants (ICICI)
# ---------------------------------------------------------------------------

_DETECT_KEYWORDS_CSV = {"Transaction Remarks", "Withdrawal Amount"}
_DETECT_KEYWORDS_PDF = {"ICICI Bank"}

_HEADER_KEYWORDS = ["Transaction Date", "Value Date"]


class ICICISavingsParser(BaseParser):
    BANK_NAME = "ICICI"

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
            return all(kw in content for kw in _DETECT_KEYWORDS_CSV)
        except Exception:
            return False

    @classmethod
    def _detect_pdf(cls, file_path: Path) -> bool:
        try:
            first_text = extract_text_pdfplumber(file_path)[:2000]
            return all(kw in first_text for kw in _DETECT_KEYWORDS_PDF)
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
        header_row_idx = find_header_row_in_file(file_path, ["Transaction Date", "Transaction Remarks"])
        if header_row_idx < 0:
            header_row_idx = find_header_row_in_file(file_path, ["Value Date", "Withdrawal"])
        if header_row_idx < 0:
            warnings.append("Could not locate ICICI CSV header row; defaulting to row 0.")
            header_row_idx = 0

        df = read_csv_flexible(file_path, skip_rows=header_row_idx, header=0)
        # Strip trailing/leading whitespace from column names (ICICI quirk)
        df.columns = [str(c).strip() for c in df.columns]

        return self._build_parse_result(df, warnings)

    def _find_header_row(
        self, raw_df: pd.DataFrame, warnings: list[str]
    ) -> int:
        for idx, row in raw_df.iterrows():
            row_str = " ".join(str(v).strip() for v in row.values if pd.notna(v))
            if "Transaction Date" in row_str or "Value Date" in row_str:
                return int(str(idx))
        warnings.append(
            "Could not locate ICICI CSV header row; defaulting to row 0."
        )
        return 0

    # ------------------------------------------------------------------
    # PDF parser
    # ------------------------------------------------------------------

    def _parse_pdf(self, file_path: Path) -> ParseResult:
        warnings: list[str] = []
        tables = extract_tables_pdfplumber(file_path)

        header: Optional[list[str]] = None
        rows: list[list[str]] = []

        for table in tables:
            for row in table:
                row_str = " ".join(row)
                if header is None and (
                    "Transaction Date" in row_str or "Value Date" in row_str
                ):
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
                warnings=["Could not find transaction table headers in ICICI PDF."],
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

        # Column discovery (strip all names again for safety)
        df.columns = [str(c).strip() for c in df.columns]

        txn_date_col = self._find_col(df, ["Transaction Date", "Txn Date"])
        val_date_col = self._find_col(df, ["Value Date"])
        remarks_col = self._find_col(df, ["Transaction Remarks", "Narration", "Description"])
        cheque_col = self._find_col(df, ["Cheque Number", "Chq No", "Reference"])
        wd_col = self._find_col(df, ["Withdrawal Amount (INR)", "Withdrawal Amount", "Debit Amount", "Debit"])
        dep_col = self._find_col(df, ["Deposit Amount (INR)", "Deposit Amount", "Credit Amount", "Credit"])
        bal_col = self._find_col(df, ["Balance (INR)", "Balance"])

        for row_idx, row in df.iterrows():
            # Use Transaction Date preferentially; fall back to Value Date
            raw_txn_date = str(row.get(txn_date_col, "")).strip() if txn_date_col else ""
            if not raw_txn_date or raw_txn_date.lower() in ("nan", ""):
                raw_txn_date = str(row.get(val_date_col, "")).strip() if val_date_col else ""

            if not raw_txn_date or raw_txn_date.lower() in ("nan", ""):
                continue

            txn_date = _safe_date(raw_txn_date)
            if txn_date is None:
                warnings.append(
                    f"Row {row_idx}: could not parse date '{raw_txn_date}'; skipping."
                )
                continue

            value_date: Optional[date] = None
            if val_date_col:
                value_date = _safe_date(str(row.get(val_date_col, "")).strip())

            description = str(row.get(remarks_col, "")).strip() if remarks_col else ""

            reference = str(row.get(cheque_col, "")).strip() if cheque_col else None
            if reference in ("nan", ""):
                reference = None

            balance: Optional[Decimal] = None
            if bal_col:
                try:
                    balance = parse_inr_amount(row.get(bal_col))
                except Exception:
                    balance = None

            # Debit / credit amounts
            wd_raw = str(row.get(wd_col, "")).strip() if wd_col else ""
            dep_raw = str(row.get(dep_col, "")).strip() if dep_col else ""

            withdrawal_amt: Optional[Decimal] = None
            deposit_amt: Optional[Decimal] = None

            if wd_raw and wd_raw not in ("nan", "", "0", "0.00"):
                try:
                    withdrawal_amt = parse_inr_amount(wd_raw)
                except Exception as e:
                    warnings.append(f"Row {row_idx}: withdrawal parse error: {e}")

            if dep_raw and dep_raw not in ("nan", "", "0", "0.00"):
                try:
                    deposit_amt = parse_inr_amount(dep_raw)
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
        """Return the first candidate column name that exists in *df*.
        Tries exact match first, then case-insensitive, then whitespace-normalised."""
        def normalise(s: str) -> str:
            return " ".join(s.lower().split())  # collapse all internal whitespace

        for c in candidates:
            # Exact match
            if c in df.columns:
                return c
            # Case-insensitive + whitespace-normalised match
            nc = normalise(c)
            for col in df.columns:
                if normalise(col) == nc:
                    return col
            # Substring match (candidate appears inside column name)
            for col in df.columns:
                if nc in normalise(col):
                    return col
        return None
