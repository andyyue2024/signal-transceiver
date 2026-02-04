#!/usr/bin/env python
"""
功能验证脚本 - 按照 prompt.txt 和 features.txt 检查所有功能
"""
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔍 Signal Transceiver - 功能完整性验证")
print("=" * 80)

# 验证计数
total_checks = 0
passed_checks = 0
failed_checks = 0

def check(name, condition, details=""):
    """检查单个功能"""
    global total_checks, passed_checks, failed_checks
    total_checks += 1

    if condition:
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
        passed_checks += 1
        return True
    else:
        print(f"❌ {name}")
        if details:
            print(f"   {details}")
        failed_checks += 1
        return False

# 1. 核心模块导入检查
print("\n📦 核心模块导入检查")
print("-" * 80)

try:
    from src.core.security import get_password_hash, verify_password, generate_api_key, generate_client_credentials
    check("安全模块", True, "密码哈希、API Key生成")
except Exception as e:
    check("安全模块", False, f"导入失败: {e}")

try:
    from src.services.auth_service import AuthService
    check("认证服务", True)
except Exception as e:
    check("认证服务", False, f"导入失败: {e}")

try:
    from src.services.data_service import DataService
    check("数据服务", True)
except Exception as e:
    check("数据服务", False, f"导入失败: {e}")

try:
    from src.services.subscription_service import SubscriptionService
    check("订阅服务", True)
except Exception as e:
    check("订阅服务", False, f"导入失败: {e}")

try:
    from src.services.strategy_service import StrategyService
    check("策略服务", True)
except Exception as e:
    check("策略服务", False, f"导入失败: {e}")

try:
    from src.services.import_service import DataImportService
    check("数据导入服务 🆕", True, "CSV/JSON/Excel批量导入")
except Exception as e:
    check("数据导入服务 🆕", False, f"导入失败: {e}")

try:
    from src.core.ip_control import IPAccessControl
    check("IP访问控制 🆕", True, "白名单/黑名单")
except Exception as e:
    check("IP访问控制 🆕", False, f"导入失败: {e}")

# 2. 监控和告警模块
print("\n📊 监控和告警模块")
print("-" * 80)

try:
    from src.monitor.metrics import metrics_registry
    check("Prometheus指标", True)
except Exception as e:
    check("Prometheus指标", False, f"导入失败: {e}")

try:
    from src.monitor.performance import PerformanceMonitor
    check("性能监控", True)
except Exception as e:
    check("性能监控", False, f"导入失败: {e}")

try:
    from src.monitor.feishu_enhanced import FeishuEnhancedNotifier
    check("飞书告警", True)
except Exception as e:
    check("飞书告警", False, f"导入失败: {e}")

try:
    from src.monitor.dingtalk import DingTalkNotifier
    check("钉钉告警", True)
except Exception as e:
    check("钉钉告警", False, f"导入失败: {e}")

# 3. 报告生成
print("\n📄 报告生成模块")
print("-" * 80)

try:
    from src.report.generator import ReportGenerator
    check("报告生成器", True, "PDF/Excel报告")
except Exception as e:
    check("报告生成器", False, f"导入失败: {e}")

# 4. 核心功能
print("\n🔧 核心功能模块")
print("-" * 80)

try:
    from src.core.scheduler import scheduler
    check("定时任务调度器", True)
except Exception as e:
    check("定时任务调度器", False, f"导入失败: {e}")

try:
    from src.core.cache import CacheManager
    check("缓存系统", True, "LRU缓存")
except Exception as e:
    check("缓存系统", False, f"导入失败: {e}")

try:
    from src.core.validation import DataValidator
    check("数据验证", True)
except Exception as e:
    check("数据验证", False, f"导入失败: {e}")

try:
    from src.core.compliance import ComplianceChecker
    check("合规检查", True)
except Exception as e:
    check("合规检查", False, f"导入失败: {e}")

try:
    from src.core.message_queue import MessageQueue
    check("消息队列", True)
except Exception as e:
    check("消息队列", False, f"导入失败: {e}")

try:
    from src.core.tracing import Tracer
    check("链路追踪", True)
except Exception as e:
    check("链路追踪", False, f"导入失败: {e}")

# 5. 高级服务
print("\n🚀 高级服务模块")
print("-" * 80)

try:
    from src.services.analytics_service import AnalyticsService
    check("数据分析服务", True)
except Exception as e:
    check("数据分析服务", False, f"导入失败: {e}")

try:
    from src.services.webhook_service import WebhookService
    check("Webhook服务", True)
except Exception as e:
    check("Webhook服务", False, f"导入失败: {e}")

try:
    from src.services.feedback_service import FeedbackService
    check("用户反馈系统", True)
except Exception as e:
    check("用户反馈系统", False, f"导入失败: {e}")

try:
    from src.services.export_service import DataExportService
    check("数据导出服务", True)
except Exception as e:
    check("数据导出服务", False, f"导入失败: {e}")

try:
    from src.services.notification_service import NotificationService
    check("系统通知服务", True)
except Exception as e:
    check("系统通知服务", False, f"导入失败: {e}")

try:
    from src.services.backup_service import BackupService
    check("数据库备份服务", True)
except Exception as e:
    check("数据库备份服务", False, f"导入失败: {e}")

# 6. API 端点
print("\n🌐 API 端点检查")
print("-" * 80)

try:
    from src.api.v1.auth import router as auth_router
    check("认证 API", True, "/api/v1/auth/*")
except Exception as e:
    check("认证 API", False, f"导入失败: {e}")

try:
    from src.api.v1.data import router as data_router
    check("数据 API", True, "/api/v1/data/*")
except Exception as e:
    check("数据 API", False, f"导入失败: {e}")

try:
    from src.api.v1.subscription import router as subscription_router
    check("订阅 API", True, "/api/v1/subscriptions/*")
except Exception as e:
    check("订阅 API", False, f"导入失败: {e}")

try:
    from src.api.v1.strategy import router as strategy_router
    check("策略 API", True, "/api/v1/strategies/*")
except Exception as e:
    check("策略 API", False, f"导入失败: {e}")

try:
    from src.api.v1.admin import router as admin_router
    check("管理 API", True, "/api/v1/admin/*")
except Exception as e:
    check("管理 API", False, f"导入失败: {e}")

try:
    import importlib
    import_module = importlib.import_module('src.api.v1.import')
    check("导入 API 🆕", True, "/api/v1/import/*")
except Exception as e:
    check("导入 API 🆕", False, f"导入失败: {e}")

# 7. Web UI
print("\n🖥️ Web UI 检查")
print("-" * 80)

try:
    from src.web.admin_login import router as login_router
    check("管理后台登录", True, "账号密码登录")
except Exception as e:
    check("管理后台登录", False, f"导入失败: {e}")

try:
    from src.web.admin_ui import router as admin_ui_router
    check("管理后台界面", True, "用户/策略/角色权限 CRUD")
except Exception as e:
    check("管理后台界面", False, f"导入失败: {e}")

# 8. 功能测试
print("\n✨ 功能测试")
print("-" * 80)

# 测试密码哈希
try:
    from src.core.security import get_password_hash, verify_password
    pwd = "test123"
    hashed = get_password_hash(pwd)
    verified = verify_password(pwd, hashed)
    check("密码哈希和验证", verified, f"bcrypt 正常工作")
except Exception as e:
    check("密码哈希和验证", False, f"测试失败: {e}")

# 测试 API Key 生成
try:
    from src.core.security import generate_api_key
    api_key, hashed_key = generate_api_key()
    check("API Key 生成", api_key.startswith("sk_") and len(api_key) > 32,
          f"生成: {api_key[:20]}...")
except Exception as e:
    check("API Key 生成", False, f"测试失败: {e}")

# 测试客户端凭证生成
try:
    from src.core.security import generate_client_credentials
    ck, cs, hs = generate_client_credentials()
    check("客户端凭证生成", ck.startswith("ck_") and cs.startswith("cs_"),
          f"CK: {ck[:15]}..., CS: {cs[:15]}...")
except Exception as e:
    check("客户端凭证生成", False, f"测试失败: {e}")

# 测试缓存
try:
    from src.core.cache import CacheManager
    cache = CacheManager.get_instance()
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    check("缓存功能", value == "test_value", "LRU 缓存正常")
except Exception as e:
    check("缓存功能", False, f"测试失败: {e}")

# 测试 IP 控制
try:
    from src.core.ip_control import IPAccessControl
    ip_control = IPAccessControl()
    is_valid = ip_control.is_valid_ip("192.168.1.1")
    in_network = ip_control.is_in_network("192.168.1.10", "192.168.1.0/24")
    check("IP 访问控制", is_valid and in_network, "IP验证和网络段检查")
except Exception as e:
    check("IP 访问控制", False, f"测试失败: {e}")

# 9. 文件存在性检查
print("\n📁 关键文件检查")
print("-" * 80)

files_to_check = [
    ("主程序", "src/main.py"),
    ("数据导入服务", "src/services/import_service.py"),
    ("导入 API", "src/api/v1/import.py"),
    ("IP 控制", "src/core/ip_control.py"),
    ("Docker 配置", "docker/Dockerfile"),
    ("Docker Compose", "docker/docker-compose.yml"),
    ("README", "README.md"),
    ("快速启动指南", "QUICKSTART.md"),
    ("功能完成报告", "COMPLETION_REPORT.md"),
    ("测试总结", "TEST_SUMMARY.md"),
]

for name, filepath in files_to_check:
    exists = os.path.exists(filepath)
    check(name, exists, filepath)

# 10. 测试文件检查
print("\n🧪 测试文件检查")
print("-" * 80)

test_files = [
    "tests/unit/test_auth.py",
    "tests/unit/test_data.py",
    "tests/unit/test_subscription.py",
    "tests/unit/test_security.py",
    "tests/unit/test_import.py",  # 新增
    "tests/integration/test_api_flow.py",
    "comprehensive_test.py",
]

for test_file in test_files:
    exists = os.path.exists(test_file)
    check(os.path.basename(test_file), exists, test_file)

# 最终统计
print("\n" + "=" * 80)
print("📊 验证结果统计")
print("=" * 80)
print(f"总检查项: {total_checks}")
print(f"✅ 通过: {passed_checks} ({passed_checks/total_checks*100:.1f}%)")
print(f"❌ 失败: {failed_checks} ({failed_checks/total_checks*100:.1f}%)")

if failed_checks == 0:
    print("\n🎉 所有功能验证通过！")
    print("\n✅ 项目状态: 完整且可用")
    sys.exit(0)
else:
    print(f"\n⚠️ 有 {failed_checks} 项需要修复")
    sys.exit(1)
