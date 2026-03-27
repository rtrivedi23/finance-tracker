from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Union
import re

import pandas as pd


_ENCODINGS = ("utf-8", "latin-1", "cp1252")


def read_csv_flexible(
    file_path: Path, skip_rows: int = 0, **kwargs
) -> pd.DataFrame:
    """Read a CSV file trying multiple encodings.

    Tries utf-8, latin-1 and cp1252 in order. Skips bad/inconsistent lines
    automatically (common in bank statements with metadata rows at the top).
    """
    last_exc: Exception | None = None
    for enc in _ENCODINGS:
        try:
            return pd.read_csv(
                file_path,
                skiprows=skip_rows,
                encoding=enc,
                on_bad_lines="skip",
                **kwargs,
            )
        except (UnicodeDecodeError, Exception) as exc:
            last_exc = exc
    raise ValueError(
        f"Could not read CSV '{file_path}' with any of {_ENCODINGS}: {last_exc}"
    )


def read_csv_raw(file_path: Path) -> pd.DataFrame:
    """Read a CSV with no header assumption and skip bad lines.
    Used to scan for the header row before a proper read."""
    for enc in _ENCODINGS:
        try:
            return pd.read_csv(
                file_path,
                header=None,
                encoding=enc,
                on_bad_lines="skip",
                dtype=str,
            )
        except Exception:
            continue
    return pd.DataFrame()


def read_excel_flexible(
    file_path: Path, skip_rows: int = 0, sheet_name: Union[str, int] = 0
) -> pd.DataFrame:
    """Read an Excel file (.xlsx or .xls).

    Parameters
    ----------
    file_path:
        Path to the Excel file.
    skip_rows:
        Number of rows to skip at the top of the sheet before the header.
    sheet_name:
        Sheet index or name to read (default: first sheet).
    """
    try:
        return pd.read_excel(
            file_path,
            skiprows=skip_rows,
            sheet_name=sheet_name,
            engine=None,  # let pandas choose openpyxl / xlrd automatically
        )
    except Exception as exc:
        raise ValueError(
            f"Could not read Excel file '{file_path}': {exc}"
        ) from exc


def find_header_row_in_file(file_path: Path, keywords: list[str]) -> int:
    """Scan a CSV file line-by-line to find the row containing all keywords.
    Returns the row index (0-based) to use as skiprows, or -1 if not found."""
    lower_keywords = [kw.lower() for kw in keywords]
    for enc in _ENCODINGS:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as f:
                for idx, line in enumerate(f):
                    line_lower = line.lower()
                    if all(kw in line_lower for kw in lower_keywords):
                        return idx
            return -1
        except Exception:
            continue
    return -1


def find_header_row(df: pd.DataFrame, keywords: list[str]) -> int:
    """Scan the rows of *df* (treating each row as potential column headers)
    and return the index of the first row that contains **all** of the given
    keywords (case-insensitive comparison).

    Parameters
    ----------
    df:
        DataFrame whose rows will be searched.
    keywords:
        A list of strings that must all be present (as substrings) in the
        candidate row.

    Returns
    -------
    int
        Row index (0-based) of the matching header row.

    Raises
    ------
    ValueError
        If no matching row is found.
    """
    lower_keywords = [kw.lower() for kw in keywords]

    for idx, row in df.iterrows():
        row_values = " ".join(str(v).lower() for v in row.values if pd.notna(v))
        if all(kw in row_values for kw in lower_keywords):
            return int(str(idx))

    raise ValueError(
        f"Could not find a header row containing all keywords: {keywords}"
    )


def parse_inr_amount(value: Union[str, float, int, None]) -> Decimal:
    """Parse an Indian-currency string or numeric value to :class:`Decimal`.

    Handles common formats encountered in Indian bank statements:

    * ``1,00,000.50``  — Indian grouping with thousands/lakhs separators
    * ``₹ 1,234.56``   — Rupee symbol prefix (with or without space)
    * ``1234.56 Dr``   — Trailing Dr/Cr suffix (sign is ignored; caller decides
                         debit/credit from the column)
    * ``(1234.56)``    — Accounting negative notation (returns absolute value)
    * ``''`` or None   — Returns ``Decimal('0')``

    Parameters
    ----------
    value:
        The raw cell value from a CSV / Excel / PDF table.

    Returns
    -------
    Decimal
        The absolute numeric value.

    Raises
    ------
    ValueError
        If the value cannot be parsed into a valid decimal number.
    """
    if value is None:
        return Decimal("0")

    if isinstance(value, (int, float)):
        return Decimal(str(abs(value)))

    text = str(value).strip()

    if not text or text in ("-", "—", "N/A", "n/a"):
        return Decimal("0")

    # Remove currency symbol, common suffixes and wrapping parentheses
    text = text.replace("₹", "").replace("Rs.", "").replace("Rs", "")
    text = re.sub(r"\s*(Dr|CR|Cr|DR)\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip("() \t")

    # Remove thousand/lakh separators (commas)
    text = text.replace(",", "").strip()

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(
            f"Cannot parse '{value}' as a decimal amount: {exc}"
        ) from exc
