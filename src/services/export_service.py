"""
Data export service for exporting data in various formats.
"""
import csv
import json
import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"  # JSON Lines format


@dataclass
class ExportResult:
    """Result of an export operation."""
    format: ExportFormat
    filename: str
    content: bytes
    record_count: int
    created_at: datetime


class DataExportService:
    """Service for exporting data in various formats."""

    def export_to_json(
        self,
        data: List[Dict[str, Any]],
        filename_prefix: str = "export"
    ) -> ExportResult:
        """Export data to JSON format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"

        # Convert datetime objects
        serializable_data = self._make_serializable(data)

        content = json.dumps(
            {"data": serializable_data, "exported_at": datetime.utcnow().isoformat()},
            ensure_ascii=False,
            indent=2
        ).encode('utf-8')

        return ExportResult(
            format=ExportFormat.JSON,
            filename=filename,
            content=content,
            record_count=len(data),
            created_at=datetime.utcnow()
        )

    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename_prefix: str = "export",
        columns: Optional[List[str]] = None
    ) -> ExportResult:
        """Export data to CSV format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"

        if not data:
            return ExportResult(
                format=ExportFormat.CSV,
                filename=filename,
                content=b"",
                record_count=0,
                created_at=datetime.utcnow()
            )

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for row in data:
            # Convert values to strings
            row_str = {k: self._to_string(v) for k, v in row.items()}
            writer.writerow(row_str)

        content = output.getvalue().encode('utf-8-sig')  # BOM for Excel

        return ExportResult(
            format=ExportFormat.CSV,
            filename=filename,
            content=content,
            record_count=len(data),
            created_at=datetime.utcnow()
        )

    def export_to_jsonl(
        self,
        data: List[Dict[str, Any]],
        filename_prefix: str = "export"
    ) -> ExportResult:
        """Export data to JSON Lines format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.jsonl"

        lines = []
        for item in data:
            serializable_item = self._make_serializable([item])[0]
            lines.append(json.dumps(serializable_item, ensure_ascii=False))

        content = '\n'.join(lines).encode('utf-8')

        return ExportResult(
            format=ExportFormat.JSONL,
            filename=filename,
            content=content,
            record_count=len(data),
            created_at=datetime.utcnow()
        )

    def export(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        filename_prefix: str = "export",
        columns: Optional[List[str]] = None
    ) -> ExportResult:
        """Export data in the specified format."""
        if format == ExportFormat.JSON:
            return self.export_to_json(data, filename_prefix)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(data, filename_prefix, columns)
        elif format == ExportFormat.JSONL:
            return self.export_to_jsonl(data, filename_prefix)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _make_serializable(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert data to JSON-serializable format."""
        result = []
        for item in data:
            serializable = {}
            for key, value in item.items():
                serializable[key] = self._to_serializable(value)
            result.append(serializable)
        return result

    def _to_serializable(self, value: Any) -> Any:
        """Convert a single value to serializable format."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            return str(value)
        return value

    def _to_string(self, value: Any) -> str:
        """Convert value to string for CSV."""
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)


# Global instance
data_export_service = DataExportService()
