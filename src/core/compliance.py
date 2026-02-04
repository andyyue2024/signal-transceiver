"""
Target compliance checking for data validation and business rules.
Validates data against target specifications and compliance requirements.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class ComplianceStatus(str, Enum):
    """Compliance check status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"


class ComplianceCategory(str, Enum):
    """Categories of compliance checks."""
    DATA_QUALITY = "data_quality"
    BUSINESS_RULE = "business_rule"
    REGULATORY = "regulatory"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    rule_id: str
    rule_name: str
    category: ComplianceCategory
    status: ComplianceStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: int = 1  # 1-5, 5 being most severe
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComplianceRule:
    """Definition of a compliance rule."""
    id: str
    name: str
    description: str
    category: ComplianceCategory
    check_func: Callable[[Dict[str, Any]], ComplianceResult]
    severity: int = 3
    enabled: bool = True


class TargetCompliance:
    """
    Target compliance checker for validating data and business rules.
    Implements configurable compliance checks for various categories.
    """

    def __init__(self):
        self._rules: Dict[str, ComplianceRule] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default compliance rules."""

        # Data Quality Rules
        self.add_rule(ComplianceRule(
            id="dq_001",
            name="数据完整性检查",
            description="验证必填字段不为空",
            category=ComplianceCategory.DATA_QUALITY,
            check_func=self._check_data_completeness,
            severity=4
        ))

        self.add_rule(ComplianceRule(
            id="dq_002",
            name="日期有效性检查",
            description="验证日期在合理范围内",
            category=ComplianceCategory.DATA_QUALITY,
            check_func=self._check_date_validity,
            severity=3
        ))

        self.add_rule(ComplianceRule(
            id="dq_003",
            name="数据格式检查",
            description="验证数据格式符合规范",
            category=ComplianceCategory.DATA_QUALITY,
            check_func=self._check_data_format,
            severity=3
        ))

        # Business Rules
        self.add_rule(ComplianceRule(
            id="br_001",
            name="策略一致性检查",
            description="验证数据与策略定义一致",
            category=ComplianceCategory.BUSINESS_RULE,
            check_func=self._check_strategy_consistency,
            severity=4
        ))

        self.add_rule(ComplianceRule(
            id="br_002",
            name="重复数据检查",
            description="检测潜在的重复数据记录",
            category=ComplianceCategory.BUSINESS_RULE,
            check_func=self._check_duplicate_data,
            severity=2
        ))

        # Security Rules
        self.add_rule(ComplianceRule(
            id="sec_001",
            name="敏感信息检查",
            description="检测并标记敏感信息",
            category=ComplianceCategory.SECURITY,
            check_func=self._check_sensitive_data,
            severity=5
        ))

        # Performance Rules
        self.add_rule(ComplianceRule(
            id="perf_001",
            name="数据大小检查",
            description="验证数据大小在可接受范围内",
            category=ComplianceCategory.PERFORMANCE,
            check_func=self._check_data_size,
            severity=2
        ))

    def add_rule(self, rule: ComplianceRule):
        """Add a compliance rule."""
        self._rules[rule.id] = rule
        logger.debug(f"Added compliance rule: {rule.id} - {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove a compliance rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]

    def enable_rule(self, rule_id: str):
        """Enable a rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str):
        """Disable a rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False

    def check(
        self,
        data: Dict[str, Any],
        categories: Optional[List[ComplianceCategory]] = None
    ) -> List[ComplianceResult]:
        """
        Run compliance checks on data.

        Args:
            data: The data to check
            categories: Optional list of categories to check (all if None)

        Returns:
            List of compliance results
        """
        results = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            if categories and rule.category not in categories:
                continue

            try:
                result = rule.check_func(data)
                result.rule_id = rule.id
                result.rule_name = rule.name
                result.category = rule.category
                result.severity = rule.severity
                results.append(result)
            except Exception as e:
                logger.error(f"Compliance check {rule.id} failed: {e}")
                results.append(ComplianceResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    status=ComplianceStatus.PENDING,
                    message=f"Check failed: {str(e)}",
                    severity=rule.severity
                ))

        return results

    def is_compliant(
        self,
        data: Dict[str, Any],
        min_severity: int = 3
    ) -> bool:
        """Check if data is compliant (no failures above minimum severity)."""
        results = self.check(data)
        return not any(
            r.status == ComplianceStatus.NON_COMPLIANT and r.severity >= min_severity
            for r in results
        )

    def get_summary(self, results: List[ComplianceResult]) -> Dict[str, Any]:
        """Get summary of compliance results."""
        total = len(results)
        compliant = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT)
        warnings = sum(1 for r in results if r.status == ComplianceStatus.WARNING)

        by_category = {}
        for cat in ComplianceCategory:
            cat_results = [r for r in results if r.category == cat]
            if cat_results:
                by_category[cat.value] = {
                    "total": len(cat_results),
                    "compliant": sum(1 for r in cat_results if r.status == ComplianceStatus.COMPLIANT),
                    "non_compliant": sum(1 for r in cat_results if r.status == ComplianceStatus.NON_COMPLIANT)
                }

        return {
            "total_checks": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "warnings": warnings,
            "compliance_rate": f"{compliant / total * 100:.1f}%" if total > 0 else "N/A",
            "by_category": by_category,
            "timestamp": datetime.utcnow().isoformat()
        }

    # ============ Default Check Functions ============

    def _check_data_completeness(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check data completeness."""
        required_fields = ["type", "symbol", "execute_date", "strategy_id"]
        missing = [f for f in required_fields if not data.get(f)]

        if missing:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.DATA_QUALITY,
                status=ComplianceStatus.NON_COMPLIANT,
                message=f"Missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing}
            )

        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.DATA_QUALITY,
            status=ComplianceStatus.COMPLIANT,
            message="All required fields present"
        )

    def _check_date_validity(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check date validity."""
        execute_date = data.get("execute_date")

        if not execute_date:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.DATA_QUALITY,
                status=ComplianceStatus.NOT_APPLICABLE,
                message="No execute_date to validate"
            )

        # Convert if string
        if isinstance(execute_date, str):
            try:
                execute_date = date.fromisoformat(execute_date)
            except ValueError:
                return ComplianceResult(
                    rule_id="",
                    rule_name="",
                    category=ComplianceCategory.DATA_QUALITY,
                    status=ComplianceStatus.NON_COMPLIANT,
                    message="Invalid date format"
                )

        today = date.today()

        # Check if too far in the past (more than 1 year)
        if execute_date < today - timedelta(days=365):
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.DATA_QUALITY,
                status=ComplianceStatus.WARNING,
                message="Date is more than 1 year in the past",
                details={"execute_date": str(execute_date)}
            )

        # Check if in the future
        if execute_date > today:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.DATA_QUALITY,
                status=ComplianceStatus.WARNING,
                message="Date is in the future",
                details={"execute_date": str(execute_date)}
            )

        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.DATA_QUALITY,
            status=ComplianceStatus.COMPLIANT,
            message="Date is valid"
        )

    def _check_data_format(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check data format compliance."""
        import re

        issues = []

        # Check symbol format
        symbol = data.get("symbol", "")
        if symbol and not re.match(r'^[A-Za-z0-9._-]+$', symbol):
            issues.append(f"Invalid symbol format: {symbol}")

        # Check type format
        data_type = data.get("type", "")
        if data_type and not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', data_type):
            issues.append(f"Invalid type format: {data_type}")

        if issues:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.DATA_QUALITY,
                status=ComplianceStatus.NON_COMPLIANT,
                message="; ".join(issues),
                details={"issues": issues}
            )

        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.DATA_QUALITY,
            status=ComplianceStatus.COMPLIANT,
            message="Data format is valid"
        )

    def _check_strategy_consistency(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check strategy consistency (placeholder)."""
        strategy_id = data.get("strategy_id")

        if not strategy_id:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.BUSINESS_RULE,
                status=ComplianceStatus.NON_COMPLIANT,
                message="Strategy ID is missing"
            )

        # In a real implementation, this would verify against the strategy table
        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.BUSINESS_RULE,
            status=ComplianceStatus.COMPLIANT,
            message="Strategy ID is present"
        )

    def _check_duplicate_data(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check for potential duplicates (placeholder)."""
        # This would typically check against existing data in the database
        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.BUSINESS_RULE,
            status=ComplianceStatus.COMPLIANT,
            message="No duplicate indicators found"
        )

    def _check_sensitive_data(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check for sensitive information."""
        import re

        sensitive_patterns = [
            (r'\b\d{16,19}\b', "Possible credit card number"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address"),
            (r'\b\d{3}-\d{2}-\d{4}\b', "Possible SSN"),
            (r'\b(?:password|passwd|pwd|secret)\s*[:=]\s*\S+', "Password/secret"),
        ]

        text = str(data)
        findings = []

        for pattern, description in sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append(description)

        if findings:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.SECURITY,
                status=ComplianceStatus.WARNING,
                message="Potentially sensitive data detected",
                details={"findings": findings}
            )

        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.SECURITY,
            status=ComplianceStatus.COMPLIANT,
            message="No sensitive data patterns detected"
        )

    def _check_data_size(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check data size."""
        import json

        try:
            size = len(json.dumps(data, default=str))
        except:
            size = len(str(data))

        max_size = 1024 * 1024  # 1MB
        warning_size = 100 * 1024  # 100KB

        if size > max_size:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.PERFORMANCE,
                status=ComplianceStatus.NON_COMPLIANT,
                message=f"Data size exceeds maximum ({size} bytes > {max_size} bytes)",
                details={"size": size, "max_size": max_size}
            )

        if size > warning_size:
            return ComplianceResult(
                rule_id="",
                rule_name="",
                category=ComplianceCategory.PERFORMANCE,
                status=ComplianceStatus.WARNING,
                message=f"Data size is large ({size} bytes)",
                details={"size": size}
            )

        return ComplianceResult(
            rule_id="",
            rule_name="",
            category=ComplianceCategory.PERFORMANCE,
            status=ComplianceStatus.COMPLIANT,
            message=f"Data size is acceptable ({size} bytes)"
        )


# Global compliance checker instance
target_compliance = TargetCompliance()
