"""
Main categorization orchestrator.
"""

from sqlalchemy.orm import Session
from app.categorizer.normalizer import normalize_description, extract_merchant_from_upi
from app.categorizer.rule_engine import RuleEngine
from app.models import Transaction


class CategorizationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = RuleEngine(db)

    def categorize(self, description: str) -> tuple[int | None, str | None]:
        """
        Run the full categorization pipeline:
        1. normalize_description()
        2. extract_merchant_from_upi() for merchant_name
        3. rule_engine.find_category()
        Returns (category_id, merchant_name) — either can be None.
        """
        normalized = normalize_description(description)
        merchant_name = extract_merchant_from_upi(description)
        category_id = self.rule_engine.find_category(description, normalized)
        return category_id, merchant_name

    def categorize_batch(self, transactions: list[Transaction]) -> None:
        """
        Categorize a list of Transaction ORM objects in place.
        Skip any with is_manually_categorized=True.
        Sets transaction.category_id and transaction.merchant_name.
        """
        for transaction in transactions:
            if transaction.is_manually_categorized:
                continue

            description = transaction.description or ""
            category_id, merchant_name = self.categorize(description)

            transaction.category_id = category_id
            if merchant_name:
                transaction.merchant_name = merchant_name

            # Also store normalized description if clean_description field exists
            if hasattr(transaction, "clean_description") and not transaction.clean_description:
                transaction.clean_description = normalize_description(description)
