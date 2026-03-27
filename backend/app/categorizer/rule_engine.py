"""
Rule-based categorization against the categorization_rules table.
"""

import re
from sqlalchemy.orm import Session
from app.models import CategorizationRule


class RuleEngine:
    def __init__(self, db: Session):
        self.db = db
        self._rules_cache: list | None = None

    def _load_rules(self) -> list:
        """Load all active rules ordered by priority ASC (lower = higher priority)."""
        rules = (
            self.db.query(CategorizationRule)
            .filter(CategorizationRule.is_active == True)
            .order_by(CategorizationRule.priority.asc())
            .all()
        )
        return rules

    def find_category(self, description: str, normalized: str) -> int | None:
        """
        Try to match normalized description against all rules.
        Returns category_id of first match, or None.
        match_type='contains': normalized contains pattern
        match_type='starts_with': normalized starts with pattern
        match_type='regex': re.search(pattern, normalized)
        """
        if self._rules_cache is None:
            self._rules_cache = self._load_rules()

        for rule in self._rules_cache:
            pattern = rule.pattern.upper()
            target = normalized.upper()

            try:
                if rule.match_type == "contains":
                    if pattern in target:
                        return rule.category_id
                elif rule.match_type == "starts_with":
                    if target.startswith(pattern):
                        return rule.category_id
                elif rule.match_type == "regex":
                    if re.search(rule.pattern, target, re.IGNORECASE):
                        return rule.category_id
            except re.error:
                # Skip malformed regex patterns
                continue

        return None

    def invalidate_cache(self):
        self._rules_cache = None
