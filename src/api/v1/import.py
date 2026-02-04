"""
Data Import API - 批量数据导入接口
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.config.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.import_service import DataImportService
from src.schemas.common import SuccessResponse
from pydantic import BaseModel


router = APIRouter(prefix="/import", tags=["Data Import"])


class ImportResultResponse(BaseModel):
    """导入结果响应"""
    total: int
    success: int
    failed: int
    success_rate: str
    errors: List[dict]


class ValidationResultResponse(BaseModel):
    """验证结果响应"""
    total: int
    valid: int
    invalid: int
    is_valid: bool
    errors: List[dict]


@router.post("/csv", response_model=ImportResultResponse)
async def import_csv(
    file: UploadFile = File(..., description="CSV file to import"),
    skip_errors: bool = Form(True, description="Skip errors and continue importing"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从 CSV 文件导入数据

    CSV 格式要求:
    - 第一行为表头：type,strategy_id,symbol,execute_date,description,metadata
    - type: 数据类型（必填）
    - strategy_id: 策略ID（必填）
    - symbol: 交易标的（必填）
    - execute_date: 执行日期，ISO格式（可选）
    - description: 描述（可选）
    - metadata: JSON格式的元数据（可选）

    示例:
    ```
    type,strategy_id,symbol,execute_date,description,metadata
    signal,1,AAPL,2024-01-01,Buy signal,"{""price"": 150.0}"
    data,2,GOOGL,2024-01-02,Market data,"{""volume"": 1000000}"
    ```
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    content = await file.read()
    csv_content = content.decode('utf-8')

    import_service = DataImportService(db)
    result = await import_service.import_from_csv(
        csv_content,
        current_user.id,
        skip_errors=skip_errors
    )

    return result.to_dict()


@router.post("/json", response_model=ImportResultResponse)
async def import_json(
    data: List[dict],
    skip_errors: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从 JSON 数据导入

    JSON 格式要求:
    ```json
    [
        {
            "type": "signal",
            "strategy_id": 1,
            "symbol": "AAPL",
            "execute_date": "2024-01-01",
            "description": "Buy signal",
            "metadata": {"price": 150.0}
        },
        {
            "type": "data",
            "strategy_id": 2,
            "symbol": "GOOGL",
            "execute_date": "2024-01-02",
            "description": "Market data",
            "metadata": {"volume": 1000000}
        }
    ]
    ```
    """
    import_service = DataImportService(db)
    result = await import_service.import_from_json(
        data,
        current_user.id,
        skip_errors=skip_errors
    )

    return result.to_dict()


@router.post("/excel", response_model=ImportResultResponse)
async def import_excel(
    file: UploadFile = File(..., description="Excel file to import"),
    sheet_name: Optional[str] = Form(None, description="Sheet name to import from"),
    skip_errors: bool = Form(True, description="Skip errors and continue importing"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从 Excel 文件导入数据

    Excel 格式要求:
    - 第一行为表头：type, strategy_id, symbol, execute_date, description, metadata
    - 数据从第二行开始

    字段说明:
    - type: 数据类型（必填）
    - strategy_id: 策略ID（必填）
    - symbol: 交易标的（必填）
    - execute_date: 执行日期（可选）
    - description: 描述（可选）
    - metadata: JSON格式的元数据（可选）
    """
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    content = await file.read()

    import_service = DataImportService(db)
    result = await import_service.import_from_excel(
        content,
        current_user.id,
        skip_errors=skip_errors,
        sheet_name=sheet_name
    )

    return result.to_dict()


@router.post("/validate", response_model=ValidationResultResponse)
async def validate_import_data(
    data: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证导入数据

    在实际导入前验证数据格式和必填字段
    不会实际写入数据库

    返回验证结果，包括:
    - total: 总记录数
    - valid: 有效记录数
    - invalid: 无效记录数
    - is_valid: 是否全部有效
    - errors: 错误详情列表
    """
    import_service = DataImportService(db)
    result = await import_service.validate_import_data(data)

    return result


@router.get("/template/csv")
async def download_csv_template():
    """
    下载 CSV 导入模板

    返回一个示例 CSV 文件，包含正确的表头和示例数据
    """
    from fastapi.responses import Response

    template = """type,strategy_id,symbol,execute_date,description,metadata
signal,1,AAPL,2024-01-01,Buy signal,"{""price"": 150.0}"
data,1,GOOGL,2024-01-02,Market data,"{""volume"": 1000000}"
alert,2,MSFT,2024-01-03,Price alert,"{""threshold"": 300.0}"
"""

    return Response(
        content=template,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=import_template.csv"
        }
    )


@router.get("/template/json")
async def download_json_template():
    """
    下载 JSON 导入模板

    返回一个示例 JSON 文件，包含正确的格式和示例数据
    """
    import json
    from fastapi.responses import Response

    template = [
        {
            "type": "signal",
            "strategy_id": 1,
            "symbol": "AAPL",
            "execute_date": "2024-01-01",
            "description": "Buy signal",
            "metadata": {"price": 150.0, "confidence": 0.85}
        },
        {
            "type": "data",
            "strategy_id": 1,
            "symbol": "GOOGL",
            "execute_date": "2024-01-02",
            "description": "Market data",
            "metadata": {"volume": 1000000, "high": 155.0, "low": 148.0}
        },
        {
            "type": "alert",
            "strategy_id": 2,
            "symbol": "MSFT",
            "execute_date": "2024-01-03",
            "description": "Price alert",
            "metadata": {"threshold": 300.0, "current": 305.0}
        }
    ]

    return Response(
        content=json.dumps(template, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=import_template.json"
        }
    )
