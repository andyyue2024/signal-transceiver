"""
Transformation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user
from src.services.transform_service import (
    transform_registry, TransformPipeline, TransformStep, TransformType
)
from src.models.user import User

router = APIRouter(prefix="/transform", tags=["Transform"])


class TransformStepIn(BaseModel):
    type: str
    field: Optional[str] = None
    to: Optional[str] = None
    value: Optional[Any] = None


class TransformRequest(BaseModel):
    pipeline: Optional[str] = None
    steps: Optional[List[TransformStepIn]] = None
    payload: Dict[str, Any]


@router.get("/pipelines", response_model=ResponseBase)
async def list_pipelines(current_user: User = Depends(get_current_user)):
    """List available transformation pipelines."""
    return ResponseBase(
        success=True,
        message="Pipelines retrieved",
        data={"pipelines": transform_registry.list_pipelines()}
    )


@router.post("/preview", response_model=ResponseBase)
async def preview_transform(
    data: TransformRequest,
    current_user: User = Depends(get_current_user)
):
    """Preview a transformation on the given payload."""
    pipeline = None
    if data.pipeline:
        pipeline = transform_registry.get(data.pipeline)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
    else:
        pipeline = TransformPipeline([
            TransformStep(
                type=TransformType(step.type),
                field=step.field,
                to=step.to,
                value=step.value
            )
            for step in (data.steps or [])
        ])

    result = pipeline.apply(data.payload)

    return ResponseBase(
        success=True,
        message="Transform applied",
        data={
            "input": result.input_data,
            "output": result.output_data,
            "warnings": result.warnings
        }
    )
