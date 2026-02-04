"""
Compliance checking API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user, get_admin_user
from src.core.compliance import target_compliance, ComplianceCategory
from src.core.validation import data_validator, strategy_validator
from src.models.user import User

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class DataValidationRequest(BaseModel):
    """Request model for data validation."""
    type: Optional[str] = None
    symbol: Optional[str] = None
    execute_date: Optional[str] = None
    strategy_id: Optional[str] = None
    description: Optional[str] = None
    payload: Optional[dict] = None


@router.post("/validate", response_model=ResponseBase)
async def validate_data(
    data: DataValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validate data against configured rules.

    Returns validation errors and warnings.
    """
    data_dict = data.model_dump(exclude_none=True)

    errors = data_validator.get_errors(data_dict)
    warnings = data_validator.get_warnings(data_dict)

    is_valid = len(errors) == 0

    return ResponseBase(
        success=is_valid,
        message="Validation passed" if is_valid else "Validation failed",
        data={
            "valid": is_valid,
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "rule": e.rule_name
                }
                for e in errors
            ],
            "warnings": [
                {
                    "field": w.field,
                    "message": w.message,
                    "rule": w.rule_name
                }
                for w in warnings
            ]
        }
    )


@router.post("/check", response_model=ResponseBase)
async def check_compliance(
    data: DataValidationRequest,
    categories: Optional[List[str]] = Query(None, description="Categories to check"),
    current_user: User = Depends(get_current_user)
):
    """
    Run compliance checks on data.

    Returns compliance status for each rule.
    """
    data_dict = data.model_dump(exclude_none=True)

    # Convert category strings to enum
    cat_enums = None
    if categories:
        cat_enums = []
        for cat in categories:
            try:
                cat_enums.append(ComplianceCategory(cat))
            except ValueError:
                pass

    results = target_compliance.check(data_dict, cat_enums)
    summary = target_compliance.get_summary(results)

    return ResponseBase(
        success=True,
        message="Compliance check completed",
        data={
            "summary": summary,
            "results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category.value,
                    "status": r.status.value,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details
                }
                for r in results
            ]
        }
    )


@router.get("/rules", response_model=ResponseBase)
async def list_compliance_rules(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """List all compliance rules."""
    rules = []

    for rule in target_compliance._rules.values():
        if category and rule.category.value != category:
            continue

        rules.append({
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "category": rule.category.value,
            "severity": rule.severity,
            "enabled": rule.enabled
        })

    return ResponseBase(
        success=True,
        message=f"Found {len(rules)} rules",
        data={"rules": rules}
    )


@router.post("/rules/{rule_id}/enable", response_model=ResponseBase)
async def enable_compliance_rule(
    rule_id: str,
    admin: User = Depends(get_admin_user)
):
    """Enable a compliance rule."""
    target_compliance.enable_rule(rule_id)

    return ResponseBase(
        success=True,
        message=f"Rule {rule_id} enabled"
    )


@router.post("/rules/{rule_id}/disable", response_model=ResponseBase)
async def disable_compliance_rule(
    rule_id: str,
    admin: User = Depends(get_admin_user)
):
    """Disable a compliance rule."""
    target_compliance.disable_rule(rule_id)

    return ResponseBase(
        success=True,
        message=f"Rule {rule_id} disabled"
    )


@router.get("/categories", response_model=ResponseBase)
async def list_categories(
    current_user: User = Depends(get_current_user)
):
    """List all compliance categories."""
    return ResponseBase(
        success=True,
        message="Categories retrieved",
        data={
            "categories": [
                {"id": cat.value, "name": cat.name}
                for cat in ComplianceCategory
            ]
        }
    )
