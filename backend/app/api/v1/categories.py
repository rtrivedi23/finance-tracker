"""
Categories API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Category, CategorizationRule

router = APIRouter(prefix="", tags=["categories"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    icon: Optional[str]
    color: Optional[str]
    is_system: bool
    display_order: int
    rule_count: int = 0

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_order: int = 0


class RuleResponse(BaseModel):
    id: int
    category_id: int
    pattern: str
    match_field: str
    match_type: str
    priority: int
    is_active: bool

    class Config:
        from_attributes = True


class RuleCreate(BaseModel):
    pattern: str
    match_type: str = "contains"
    priority: int = 100
    match_field: str = "description"


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """List all categories with their rule counts."""
    categories = db.query(Category).order_by(Category.display_order.asc()).all()

    # Build rule counts in one query
    rule_counts = (
        db.query(CategorizationRule.category_id, func.count(CategorizationRule.id).label("cnt"))
        .group_by(CategorizationRule.category_id)
        .all()
    )
    count_map = {row.category_id: row.cnt for row in rule_counts}

    result = []
    for cat in categories:
        result.append(
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                parent_id=cat.parent_id,
                icon=cat.icon,
                color=cat.color,
                is_system=cat.is_system,
                display_order=cat.display_order,
                rule_count=count_map.get(cat.id, 0),
            )
        )
    return result


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    """Create a custom (non-system) category."""
    category = Category(
        name=payload.name,
        parent_id=payload.parent_id,
        icon=payload.icon,
        color=payload.color,
        display_order=payload.display_order,
        is_system=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        icon=category.icon,
        color=category.color,
        is_system=category.is_system,
        display_order=category.display_order,
        rule_count=0,
    )


@router.get("/{category_id}/rules", response_model=list[RuleResponse])
def list_rules_for_category(category_id: int, db: Session = Depends(get_db)):
    """List all categorization rules for a given category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    rules = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.category_id == category_id)
        .order_by(CategorizationRule.priority.asc())
        .all()
    )
    return rules


@router.post("/{category_id}/rules", response_model=RuleResponse, status_code=201)
def add_rule(category_id: int, payload: RuleCreate, db: Session = Depends(get_db)):
    """Add a new rule to a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    rule = CategorizationRule(
        category_id=category_id,
        pattern=payload.pattern,
        match_field=payload.match_field,
        match_type=payload.match_type,
        priority=payload.priority,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a categorization rule."""
    rule = db.query(CategorizationRule).filter(CategorizationRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
