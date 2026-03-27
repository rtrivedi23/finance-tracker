"""HDFC Bank Credit Card statement parser. Handles CSV format."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.parsers.base import BaseParser, ParseResult, RawTransaction
from app.parsers.csv_utils import read_csv_flexible, parse_inr_amount, find_header_row_in_file


class HDFCCreditParser(BaseParser):
    BANK_NAME = "HDFC"

    @classmethod
    def detect(cls, file_path: Path) -> bool:
        if file_path.suffix.lower() not in (".csv",):
            return False
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2000).upper()
            return "HDFC" in content and (
                "CREDIT CARD" in content or "CARD NO" in content or "REWARD POINTS" in content
            )
        except Exception:
            return False

    def parse(self, file_path: Path) -> ParseResult:
        return self._parse_csv(file_path)

    def _parse_csv(self, file_path: Path) -> ParseResult:
        warnings: list[str] = []

        # Find header row by scanning file raw
        header_idx = find_header_row_in_file(file_path, ["date", "description"])
        if header_idx < 0:
            header_idx = find_header_row_in_file(file_path, ["date", "amount"])
        if header_idx < 0:
            warnings.append("Could not find header row; attempting first row as header")
            header_idx = 0

        df = read_csv_flexible(file_path, skip_rows=header_idx)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Normalize column names
        col_map = {}
        for col in df.columns:
            if "date" in col:
                col_map.setdefault("date", col)
            if "description" in col or "narration" in col or "particulars" in col or "detail" in col:
                col_map.setdefault("description", col)
            if "debit" in col or ("amount" in col and "credit" not in col):
                col_map.setdefault("debit", col)
            if "credit" in col:
                col_map.setdefault("credit", col)
            if col == "amount":
                col_map.setdefault("amount", col)

        if "date" not in col_map or "description" not in col_map:
            warnings.append("Missing required columns (date/description). Parsing may be incomplete.")
            return ParseResult([], None, None, None, self.BANK_NAME, warnings)

        transactions: list[RawTransaction] = []
        period_from: date | None = None
        period_to: date | None = None

        for _, row in df.iterrows():
            try:
                raw_date = str(row[col_map["date"]]).strip()
                if not raw_date or raw_date.lower() in ("nan", "date"):
                    continue

                txn_date = self._parse_date(raw_date)
                if txn_date is None:
                    continue

                description = str(row[col_map["description"]]).strip()
                if not description or description.lower() in ("nan", "description"):
                    continue

                # Determine amount and type
                amount = Decimal("0")
                txn_type = "debit"

                if "debit" in col_map and "credit" in col_map:
                    debit_val = str(row.get(col_map["debit"], "")).strip()
                    credit_val = str(row.get(col_map["credit"], "")).strip()
                    if debit_val and debit_val.lower() not in ("nan", "", "0"):
                        amount = parse_inr_amount(debit_val)
                        txn_type = "debit"
                    elif credit_val and credit_val.lower() not in ("nan", "", "0"):
                        amount = parse_inr_amount(credit_val)
                        txn_type = "credit"
                    else:
                        continue
                elif "amount" in col_map:
                    raw_amt = str(row[col_map["amount"]]).strip()
                    if raw_amt.lower() in ("nan", ""):
                        continue
                    # Credit card: positive = debit (spending), negative = credit (payment)
                    if raw_amt.startswith("-") or "cr" in raw_amt.lower():
                        txn_type = "credit"
                        raw_amt = raw_amt.lstrip("-").replace("Cr", "").replace("CR", "").strip()
                    amount = parse_inr_amount(raw_amt)
                else:
                    continue

                if amount <= 0:
                    continue

                if period_from is None or txn_date < period_from:
                    period_from = txn_date
                if period_to is None or txn_date > period_to:
                    period_to = txn_date

                transactions.append(RawTransaction(
                    date=txn_date,
                    description=description,
                    amount=amount,
                    type=txn_type,
                    raw_row=row.to_dict(),
                ))

            except Exception as e:
                warnings.append(f"Skipped row: {e}")
                continue

        return ParseResult(
            transactions=transactions,
            period_from=period_from,
            period_to=period_to,
            account_number=None,
            bank_name=self.BANK_NAME,
            warnings=warnings,
        )

    @staticmethod
    def _parse_date(raw: str):
        from dateutil import parser as dateparser
        try:
            return dateparser.parse(raw, dayfirst=True).date()
        except Exception:
            return None
