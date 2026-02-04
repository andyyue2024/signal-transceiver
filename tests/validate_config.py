"""
Environment Configuration Validator
Validates .env configuration and provides recommendations
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigValidator:
    """Validate environment configuration."""

    def __init__(self, env_file: str = "../.env"):
        self.env_file = env_file
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def validate(self) -> Tuple[bool, Dict]:
        """Run all validation checks."""
        print(f"🔍 Validating {self.env_file}...")
        print("=" * 60)

        # Check if file exists
        if not os.path.exists(self.env_file):
            self.errors.append(f"{self.env_file} file not found")
            return False, self._get_report()

        # Load environment variables
        config = self._load_env()

        # Run validation checks
        self._check_security(config)
        self._check_database(config)
        self._check_production_ready(config)
        self._check_monitoring(config)
        self._check_performance(config)

        # Generate report
        is_valid = len(self.errors) == 0
        return is_valid, self._get_report()

    def _load_env(self) -> Dict[str, str]:
        """Load environment variables from file."""
        config = {}
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config

    def _check_security(self, config: Dict[str, str]):
        """Check security-related configurations."""
        # Check SECRET_KEY
        secret = config.get('SECRET_KEY', '')
        if 'change' in secret.lower() or 'dev' in secret.lower():
            self.errors.append("SECRET_KEY contains 'change' or 'dev' - must be changed in production")
        if len(secret) < 32:
            self.warnings.append("SECRET_KEY should be at least 32 characters")

        # Check ADMIN_API_KEY
        admin_key = config.get('ADMIN_API_KEY', '')
        if 'change' in admin_key.lower():
            self.errors.append("ADMIN_API_KEY must be changed before deployment")

        # Check DEBUG mode
        if config.get('DEBUG', '').lower() == 'true':
            self.warnings.append("DEBUG=true - should be false in production")

        # Check API key rotation
        rotation_days = config.get('API_KEY_ROTATION_DAYS', '90')
        if int(rotation_days) > 180:
            self.recommendations.append(f"API_KEY_ROTATION_DAYS={rotation_days} - consider shorter rotation period")

    def _check_database(self, config: Dict[str, str]):
        """Check database configurations."""
        db_url = config.get('DATABASE_URL', '')

        if 'sqlite' in db_url:
            self.recommendations.append("Using SQLite - consider MySQL/PostgreSQL for production")

        if config.get('DEBUG', '').lower() == 'false' and 'sqlite' in db_url:
            self.warnings.append("Production mode with SQLite - not recommended for high load")

        # Check pool settings
        pool_size = int(config.get('DB_POOL_SIZE', '20'))
        if pool_size < 10:
            self.recommendations.append(f"DB_POOL_SIZE={pool_size} - consider increasing for production")

    def _check_production_ready(self, config: Dict[str, str]):
        """Check production readiness."""
        debug = config.get('DEBUG', '').lower() == 'true'
        enable_docs = config.get('ENABLE_DOCS', '').lower() == 'true'
        enable_redoc = config.get('ENABLE_REDOC', '').lower() == 'true'

        if not debug:  # Production mode
            if enable_docs or enable_redoc:
                self.warnings.append("API docs are enabled in production - consider disabling for security")

            if not config.get('PROMETHEUS_ENABLED', '').lower() == 'true':
                self.recommendations.append("Enable Prometheus monitoring in production")

            if not config.get('AUDIT_LOG_ENABLED', '').lower() == 'true':
                self.warnings.append("Audit logging is disabled - enable for compliance")

    def _check_monitoring(self, config: Dict[str, str]):
        """Check monitoring configurations."""
        if config.get('PROMETHEUS_ENABLED', '').lower() != 'true':
            self.recommendations.append("Enable Prometheus for better monitoring")

        if not config.get('FEISHU_ENABLED', '').lower() == 'true' and \
           not config.get('DINGTALK_ENABLED', '').lower() == 'true' and \
           not config.get('EMAIL_ENABLED', '').lower() == 'true':
            self.recommendations.append("No alert channels enabled - configure Feishu/DingTalk/Email")

        if config.get('AUTO_BACKUP_ENABLED', '').lower() != 'true':
            self.warnings.append("Auto backup is disabled - enable for data safety")

    def _check_performance(self, config: Dict[str, str]):
        """Check performance configurations."""
        if config.get('CACHE_ENABLED', '').lower() != 'true':
            self.recommendations.append("Enable caching for better performance")

        workers = int(config.get('ASYNC_WORKERS', '4'))
        if workers < 4:
            self.recommendations.append(f"ASYNC_WORKERS={workers} - consider 4-8 for production")

        if config.get('RATE_LIMIT_ENABLED', '').lower() != 'true':
            self.warnings.append("Rate limiting is disabled - enable to prevent abuse")

    def _get_report(self) -> Dict:
        """Generate validation report."""
        report = {
            'errors': self.errors,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'total_issues': len(self.errors) + len(self.warnings)
        }
        return report

    def print_report(self, report: Dict):
        """Print formatted validation report."""
        print()

        if report['errors']:
            print("❌ ERRORS (must fix):")
            for i, error in enumerate(report['errors'], 1):
                print(f"  {i}. {error}")
            print()

        if report['warnings']:
            print("⚠️  WARNINGS (should fix):")
            for i, warning in enumerate(report['warnings'], 1):
                print(f"  {i}. {warning}")
            print()

        if report['recommendations']:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()

        print("=" * 60)
        if not report['errors'] and not report['warnings']:
            print("✅ Configuration is valid!")
        elif not report['errors']:
            print(f"⚠️  Configuration has {len(report['warnings'])} warnings")
        else:
            print(f"❌ Configuration has {report['total_issues']} issues")
        print("=" * 60)


def main():
    """Main function."""
    validator = ConfigValidator()
    is_valid, report = validator.validate()
    validator.print_report(report)

    return 0 if is_valid else 1


if __name__ == "__main__":
    exit(main())
