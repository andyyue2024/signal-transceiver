"""
Data transformation pipeline service.
Provides reusable transformations for payload normalization.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from datetime import datetime


class TransformType(str, Enum):
    """Supported transform types."""
    TRIM = "trim"
    UPPER = "upper"
    LOWER = "lower"
    RENAME = "rename"
    ADD_FIELD = "add_field"
    REMOVE_FIELD = "remove_field"


@dataclass
class TransformStep:
    """Single transformation step."""
    type: TransformType
    field: Optional[str] = None
    to: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class TransformResult:
    """Result of applying transformations."""
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    applied_steps: List[TransformStep]
    warnings: List[str] = field(default_factory=list)
    transformed_at: datetime = field(default_factory=datetime.utcnow)


class TransformPipeline:
    """Applies a list of transformation steps to a payload."""

    def __init__(self, steps: Optional[List[TransformStep]] = None):
        self.steps = steps or []

    def add_step(self, step: TransformStep) -> "TransformPipeline":
        self.steps.append(step)
        return self

    def apply(self, payload: Dict[str, Any]) -> TransformResult:
        data = dict(payload)
        warnings: List[str] = []

        for step in self.steps:
            if step.type == TransformType.TRIM and step.field:
                value = data.get(step.field)
                if isinstance(value, str):
                    data[step.field] = value.strip()
            elif step.type == TransformType.UPPER and step.field:
                value = data.get(step.field)
                if isinstance(value, str):
                    data[step.field] = value.upper()
            elif step.type == TransformType.LOWER and step.field:
                value = data.get(step.field)
                if isinstance(value, str):
                    data[step.field] = value.lower()
            elif step.type == TransformType.RENAME and step.field and step.to:
                if step.field in data:
                    data[step.to] = data.pop(step.field)
                else:
                    warnings.append(f"Missing field for rename: {step.field}")
            elif step.type == TransformType.ADD_FIELD and step.to:
                data[step.to] = step.value
            elif step.type == TransformType.REMOVE_FIELD and step.field:
                data.pop(step.field, None)
            else:
                warnings.append(f"Unsupported or invalid step: {step}")

        return TransformResult(
            input_data=payload,
            output_data=data,
            applied_steps=self.steps,
            warnings=warnings
        )


class TransformRegistry:
    """Registry of named pipelines."""

    def __init__(self):
        self._pipelines: Dict[str, TransformPipeline] = {}
        self._init_defaults()

    def _init_defaults(self):
        self._pipelines["normalize_symbol"] = TransformPipeline([
            TransformStep(type=TransformType.TRIM, field="symbol"),
            TransformStep(type=TransformType.UPPER, field="symbol")
        ])
        self._pipelines["normalize_type"] = TransformPipeline([
            TransformStep(type=TransformType.TRIM, field="type"),
            TransformStep(type=TransformType.LOWER, field="type")
        ])

    def list_pipelines(self) -> List[str]:
        return sorted(self._pipelines.keys())

    def get(self, name: str) -> Optional[TransformPipeline]:
        return self._pipelines.get(name)

    def register(self, name: str, pipeline: TransformPipeline):
        self._pipelines[name] = pipeline


transform_registry = TransformRegistry()
