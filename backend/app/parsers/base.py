from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal


@dataclass
class RawTransaction:
    date: date
    description: str
    amount: Decimal
    type: Literal["debit", "credit"]
    value_date: date | None = None
    reference: str | None = None
    balance: Decimal | None = None
    raw_row: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    transactions: list[RawTransaction]
    period_from: date | None
    period_to: date | None
    account_number: str | None  # typically last 4 digits
    bank_name: str
    warnings: list[str] = field(default_factory=list)


class BaseParser(ABC):
    """Abstract base class that every bank parser must implement."""

    @classmethod
    @abstractmethod
    def detect(cls, file_path: Path) -> bool:
        """Return True if this parser can handle the given file."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """Parse the file and return a structured ParseResult."""
