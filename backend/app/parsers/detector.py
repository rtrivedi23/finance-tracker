from pathlib import Path
from typing import Optional

from app.parsers.base import BaseParser
from app.parsers.banks.hdfc_savings import HDFCSavingsParser
from app.parsers.banks.hdfc_credit import HDFCCreditParser
from app.parsers.banks.icici_savings import ICICISavingsParser
from app.parsers.banks.generic_csv import GenericCSVParser

# Order matters: more-specific parsers first, GenericCSVParser always last as fallback.
REGISTERED_PARSERS: list[type[BaseParser]] = [
    HDFCCreditParser,   # before HDFCSavings so credit card CSVs are caught first
    HDFCSavingsParser,
    ICICISavingsParser,
    GenericCSVParser,
]


def detect_parser(file_path: Path) -> Optional[BaseParser]:
    """Try each registered parser's detect() method in order.

    Returns the first matching parser instance, or None if no parser
    recognises the file.
    """
    for parser_cls in REGISTERED_PARSERS:
        try:
            if parser_cls.detect(file_path):
                return parser_cls()
        except Exception as exc:
            # A broken detect() should not prevent other parsers from running.
            print(f"[WARNING] {parser_cls.__name__}.detect() raised: {exc}")
    return None
