"""
Seeds default categories and rules into the database on first run.
"""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Category, CategorizationRule

SEEDS_DIR = Path(__file__).parent.parent / "categorizer" / "seeds"


def seed_default_data(db: Session) -> None:
    """
    If categories table is empty:
    1. Load default_categories.json, insert all Category rows
    2. Load default_rules.json, match each rule's category_name to inserted category id,
       insert CategorizationRule rows
    3. Print "Seeded X categories and Y rules"
    If categories already exist, skip silently.
    """
    existing_count = db.query(Category).count()
    if existing_count > 0:
        return

    # Load and insert categories
    categories_path = SEEDS_DIR / "default_categories.json"
    with open(categories_path, "r", encoding="utf-8") as f:
        categories_data = json.load(f)

    category_map: dict[str, int] = {}
    inserted_categories = 0

    for cat_data in categories_data:
        category = Category(
            name=cat_data["name"],
            icon=cat_data.get("icon"),
            color=cat_data.get("color"),
            display_order=cat_data.get("display_order", 0),
            is_system=True,
            parent_id=None,
        )
        db.add(category)
        db.flush()  # flush to get the auto-generated id
        category_map[cat_data["name"]] = category.id
        inserted_categories += 1

    # Load and insert rules
    rules_path = SEEDS_DIR / "default_rules.json"
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    inserted_rules = 0

    for rule_data in rules_data:
        category_name = rule_data.get("category_name")
        category_id = category_map.get(category_name)
        if category_id is None:
            # Skip rules for unknown categories
            continue

        rule = CategorizationRule(
            category_id=category_id,
            pattern=rule_data["pattern"],
            match_field="description",
            match_type=rule_data.get("match_type", "contains"),
            priority=rule_data.get("priority", 100),
            is_active=True,
        )
        db.add(rule)
        inserted_rules += 1

    db.commit()
    print(f"Seeded {inserted_categories} categories and {inserted_rules} rules")
