"""
Clean and normalize transaction descriptions for matching.
"""

import re


def normalize_description(text: str) -> str:
    """
    1. Uppercase
    2. Strip leading/trailing whitespace
    3. Remove UPI reference numbers (long digit sequences like /123456789012)
    4. Remove NEFT/IMPS UTR numbers (typically 12+ digits)
    5. Normalize multiple spaces to single space
    6. Remove special chars except alphanumeric, spaces, hyphens, slashes
    Returns cleaned text suitable for rule matching.
    """
    if not text:
        return ""

    # Step 1: Uppercase
    text = text.upper()

    # Step 2: Strip leading/trailing whitespace
    text = text.strip()

    # Step 3: Remove UPI reference numbers (slash followed by 9+ digits)
    text = re.sub(r"/\d{9,}", "", text)

    # Step 4: Remove NEFT/IMPS UTR numbers (standalone 12+ digit sequences)
    text = re.sub(r"\b\d{12,}\b", "", text)

    # Step 5 (pre): Remove special chars except alphanumeric, spaces, hyphens, slashes, dots
    text = re.sub(r"[^A-Z0-9 \-/.]", " ", text)

    # Step 5: Normalize multiple spaces to single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_prefix(text: str) -> str | None:
    """Extract transaction type prefix: UPI, NEFT, IMPS, ATM, POS, NACH, BBPS, EMI, etc."""
    if not text:
        return None

    upper = text.upper().strip()

    prefixes = [
        "UPI", "NEFT", "IMPS", "RTGS",
        "ATM", "POS", "NACH", "BBPS",
        "EMI", "ACH", "ECS", "ENACH",
        "NETBANKING", "INTERNET BANKING",
        "MOBILE BANKING", "BILL PAYMENT",
        "CHEQUE", "CHQ", "DD",
    ]

    for prefix in prefixes:
        if upper.startswith(prefix):
            return prefix

    return None


def extract_merchant_from_upi(text: str) -> str | None:
    """
    UPI descriptions look like: UPI-SWIGGY INDIA PRIVATE-user@okaxis-...-...
    Extract the merchant name portion (2nd segment after UPI-).
    Return None if pattern doesn't match.
    """
    if not text:
        return None

    upper = text.upper().strip()

    # Match UPI- followed by merchant name (second segment)
    # Pattern: UPI-<MERCHANT>-<upi_id>-...
    match = re.match(r"UPI[-/]([^-/]+)[-/]", upper)
    if match:
        merchant = match.group(1).strip()
        # Filter out very short or clearly non-merchant values
        if len(merchant) >= 3:
            return merchant.title()

    return None
