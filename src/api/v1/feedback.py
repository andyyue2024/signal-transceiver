"""
Feedback API endpoints for user support.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user
from src.services.feedback_service import (
    feedback_service, FeedbackType, FeedbackStatus, FeedbackPriority
)
from src.models.user import User

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackCreate(BaseModel):
    """Request to create feedback."""
    title: str
    description: str
    type: str = "other"
    priority: str = "medium"
    tags: Optional[List[str]] = None


class FeedbackUpdate(BaseModel):
    """Request to update feedback."""
    status: Optional[str] = None
    response: Optional[str] = None


@router.post("", response_model=ResponseBase)
async def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Submit user feedback.

    Types: bug, feature_request, question, improvement, other
    Priority: low, medium, high, critical
    """
    try:
        feedback_type = FeedbackType(data.type)
    except ValueError:
        feedback_type = FeedbackType.OTHER

    try:
        priority = FeedbackPriority(data.priority)
    except ValueError:
        priority = FeedbackPriority.MEDIUM

    feedback = feedback_service.submit(
        title=data.title,
        description=data.description,
        feedback_type=feedback_type,
        user_id=current_user.id,
        priority=priority,
        tags=data.tags
    )

    return ResponseBase(
        success=True,
        message="Feedback submitted successfully",
        data=feedback.to_dict()
    )


@router.get("", response_model=ResponseBase)
async def list_feedbacks(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """List user's feedbacks."""
    status_filter = FeedbackStatus(status) if status else None
    type_filter = FeedbackType(type) if type else None

    feedbacks = feedback_service.list_feedbacks(
        status=status_filter,
        feedback_type=type_filter,
        user_id=current_user.id,
        limit=limit
    )

    return ResponseBase(
        success=True,
        message=f"Found {len(feedbacks)} feedbacks",
        data={
            "feedbacks": [f.to_dict() for f in feedbacks]
        }
    )


@router.get("/stats", response_model=ResponseBase)
async def get_feedback_stats(
    current_user: User = Depends(get_current_user)
):
    """Get feedback statistics."""
    return ResponseBase(
        success=True,
        message="Feedback statistics",
        data=feedback_service.get_stats()
    )


@router.get("/{feedback_id}", response_model=ResponseBase)
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get feedback details."""
    feedback = feedback_service.get(feedback_id)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Users can only see their own feedback
    if feedback.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    return ResponseBase(
        success=True,
        message="Feedback found",
        data=feedback.to_dict()
    )


@router.get("/types", response_model=ResponseBase)
async def get_feedback_types():
    """Get available feedback types."""
    return ResponseBase(
        success=True,
        message="Feedback types",
        data={
            "types": [t.value for t in FeedbackType],
            "priorities": [p.value for p in FeedbackPriority],
            "statuses": [s.value for s in FeedbackStatus]
        }
    )
