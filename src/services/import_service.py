"""
Data Import Service - 批量数据导入功能
支持 CSV, JSON, Excel 格式的数据导入
"""
import csv
import json
from io import StringIO, BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.data import Data
from src.models.strategy import Strategy
from src.core.exceptions import ValidationError, NotFoundError


class ImportResult:
    """导入结果"""
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.errors: List[Dict[str, Any]] = []

    def add_success(self):
        self.success += 1

    def add_error(self, row: int, error: str, data: Optional[Dict] = None):
        self.failed += 1
        self.errors.append({
            "row": row,
            "error": error,
            "data": data
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "success_rate": f"{(self.success/self.total*100):.2f}%" if self.total > 0 else "0%",
            "errors": self.errors
        }


class DataImportService:
    """数据导入服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_from_csv(
        self,
        csv_content: str,
        user_id: int,
        skip_errors: bool = True
    ) -> ImportResult:
        """
        从 CSV 导入数据

        CSV 格式:
        type,strategy_id,symbol,execute_date,description,metadata
        signal,1,AAPL,2024-01-01,Buy signal,{"price": 150.0}
        """
        result = ImportResult()

        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
        result.total = len(rows)

        for idx, row in enumerate(rows, start=1):
            try:
                # 验证必填字段
                if not all([row.get('type'), row.get('strategy_id'), row.get('symbol')]):
                    raise ValidationError("Missing required fields: type, strategy_id, symbol")

                # 验证策略是否存在
                strategy_id = int(row['strategy_id'])
                strategy_result = await self.db.execute(
                    select(Strategy).where(Strategy.id == strategy_id)
                )
                strategy = strategy_result.scalar_one_or_none()
                if not strategy:
                    raise NotFoundError("Strategy", strategy_id)

                # 解析元数据
                metadata = {}
                if row.get('metadata'):
                    try:
                        metadata = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        metadata = {"raw": row['metadata']}

                # 解析执行日期
                execute_date = None
                if row.get('execute_date'):
                    try:
                        execute_date = datetime.fromisoformat(row['execute_date'])
                    except ValueError:
                        pass

                # 创建数据记录
                data = Data(
                    type=row['type'].strip(),
                    strategy_id=strategy_id,
                    symbol=row['symbol'].strip(),
                    execute_date=execute_date,
                    description=row.get('description', '').strip() or None,
                    metadata=metadata,
                    user_id=user_id,
                    created_at=datetime.now(timezone.utc)
                )

                self.db.add(data)
                result.add_success()

            except Exception as e:
                result.add_error(idx, str(e), dict(row))
                if not skip_errors:
                    await self.db.rollback()
                    raise

        # 提交所有成功的记录
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to commit data: {str(e)}")

        return result

    async def import_from_json(
        self,
        json_data: List[Dict[str, Any]],
        user_id: int,
        skip_errors: bool = True
    ) -> ImportResult:
        """
        从 JSON 导入数据

        JSON 格式:
        [
            {
                "type": "signal",
                "strategy_id": 1,
                "symbol": "AAPL",
                "execute_date": "2024-01-01",
                "description": "Buy signal",
                "metadata": {"price": 150.0}
            }
        ]
        """
        result = ImportResult()
        result.total = len(json_data)

        for idx, item in enumerate(json_data, start=1):
            try:
                # 验证必填字段
                if not all([item.get('type'), item.get('strategy_id'), item.get('symbol')]):
                    raise ValidationError("Missing required fields: type, strategy_id, symbol")

                # 验证策略是否存在
                strategy_id = int(item['strategy_id'])
                strategy_result = await self.db.execute(
                    select(Strategy).where(Strategy.id == strategy_id)
                )
                strategy = strategy_result.scalar_one_or_none()
                if not strategy:
                    raise NotFoundError("Strategy", strategy_id)

                # 解析执行日期
                execute_date = None
                if item.get('execute_date'):
                    if isinstance(item['execute_date'], str):
                        try:
                            execute_date = datetime.fromisoformat(item['execute_date'])
                        except ValueError:
                            pass
                    elif isinstance(item['execute_date'], datetime):
                        execute_date = item['execute_date']

                # 创建数据记录
                data = Data(
                    type=str(item['type']).strip(),
                    strategy_id=strategy_id,
                    symbol=str(item['symbol']).strip(),
                    execute_date=execute_date,
                    description=item.get('description', '').strip() or None,
                    metadata=item.get('metadata', {}),
                    user_id=user_id,
                    created_at=datetime.now(timezone.utc)
                )

                self.db.add(data)
                result.add_success()

            except Exception as e:
                result.add_error(idx, str(e), item)
                if not skip_errors:
                    await self.db.rollback()
                    raise

        # 提交所有成功的记录
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to commit data: {str(e)}")

        return result

    async def import_from_excel(
        self,
        excel_bytes: bytes,
        user_id: int,
        skip_errors: bool = True,
        sheet_name: str = None
    ) -> ImportResult:
        """
        从 Excel 导入数据
        需要安装 openpyxl
        """
        try:
            import openpyxl
        except ImportError:
            raise ValidationError("openpyxl is required for Excel import. Install it with: pip install openpyxl")

        result = ImportResult()

        try:
            workbook = openpyxl.load_workbook(BytesIO(excel_bytes))
            sheet = workbook[sheet_name] if sheet_name else workbook.active

            # 读取表头
            headers = [cell.value for cell in sheet[1]]

            # 读取数据行
            rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_dict = dict(zip(headers, row))
                rows.append(row_dict)

            result.total = len(rows)

            for idx, row in enumerate(rows, start=2):  # Excel 行号从2开始（1是表头）
                try:
                    # 验证必填字段
                    if not all([row.get('type'), row.get('strategy_id'), row.get('symbol')]):
                        raise ValidationError("Missing required fields: type, strategy_id, symbol")

                    # 验证策略是否存在
                    strategy_id = int(row['strategy_id'])
                    strategy_result = await self.db.execute(
                        select(Strategy).where(Strategy.id == strategy_id)
                    )
                    strategy = strategy_result.scalar_one_or_none()
                    if not strategy:
                        raise NotFoundError("Strategy", strategy_id)

                    # 解析执行日期
                    execute_date = None
                    if row.get('execute_date'):
                        if isinstance(row['execute_date'], datetime):
                            execute_date = row['execute_date']
                        elif isinstance(row['execute_date'], str):
                            try:
                                execute_date = datetime.fromisoformat(row['execute_date'])
                            except ValueError:
                                pass

                    # 解析元数据
                    metadata = {}
                    if row.get('metadata'):
                        if isinstance(row['metadata'], dict):
                            metadata = row['metadata']
                        elif isinstance(row['metadata'], str):
                            try:
                                metadata = json.loads(row['metadata'])
                            except json.JSONDecodeError:
                                metadata = {"raw": row['metadata']}

                    # 创建数据记录
                    data = Data(
                        type=str(row['type']).strip(),
                        strategy_id=strategy_id,
                        symbol=str(row['symbol']).strip(),
                        execute_date=execute_date,
                        description=str(row.get('description', '')).strip() or None,
                        metadata=metadata,
                        user_id=user_id,
                        created_at=datetime.now(timezone.utc)
                    )

                    self.db.add(data)
                    result.add_success()

                except Exception as e:
                    result.add_error(idx, str(e), row)
                    if not skip_errors:
                        await self.db.rollback()
                        raise

            # 提交所有成功的记录
            try:
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                raise ValidationError(f"Failed to commit data: {str(e)}")

        except Exception as e:
            raise ValidationError(f"Failed to read Excel file: {str(e)}")

        return result

    async def validate_import_data(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证导入数据，返回验证结果
        不会实际导入数据
        """
        errors = []
        valid_count = 0

        for idx, item in enumerate(data, start=1):
            item_errors = []

            # 检查必填字段
            required_fields = ['type', 'strategy_id', 'symbol']
            for field in required_fields:
                if not item.get(field):
                    item_errors.append(f"Missing required field: {field}")

            # 验证数据类型
            if item.get('strategy_id'):
                try:
                    int(item['strategy_id'])
                except ValueError:
                    item_errors.append("strategy_id must be an integer")

            # 验证日期格式
            if item.get('execute_date') and isinstance(item['execute_date'], str):
                try:
                    datetime.fromisoformat(item['execute_date'])
                except ValueError:
                    item_errors.append("Invalid date format for execute_date. Use ISO format (YYYY-MM-DD)")

            if item_errors:
                errors.append({
                    "row": idx,
                    "errors": item_errors,
                    "data": item
                })
            else:
                valid_count += 1

        return {
            "total": len(data),
            "valid": valid_count,
            "invalid": len(errors),
            "errors": errors,
            "is_valid": len(errors) == 0
        }
