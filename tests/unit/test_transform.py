"""
Tests for transform service.
"""
from src.services.transform_service import (
    TransformPipeline, TransformStep, TransformType, transform_registry
)


def test_registry_defaults():
    pipelines = transform_registry.list_pipelines()
    assert "normalize_symbol" in pipelines
    assert "normalize_type" in pipelines


def test_pipeline_apply():
    pipeline = TransformPipeline([
        TransformStep(type=TransformType.TRIM, field="symbol"),
        TransformStep(type=TransformType.UPPER, field="symbol"),
        TransformStep(type=TransformType.RENAME, field="symbol", to="ticker"),
        TransformStep(type=TransformType.ADD_FIELD, to="source", value="api")
    ])

    payload = {"symbol": "  aapl  ", "type": "signal"}
    result = pipeline.apply(payload)

    assert result.output_data["ticker"] == "AAPL"
    assert result.output_data["source"] == "api"
    assert "symbol" not in result.output_data


def test_pipeline_remove_field():
    pipeline = TransformPipeline([
        TransformStep(type=TransformType.REMOVE_FIELD, field="internal")
    ])

    payload = {"internal": "x", "public": "y"}
    result = pipeline.apply(payload)

    assert "internal" not in result.output_data
    assert result.output_data["public"] == "y"
