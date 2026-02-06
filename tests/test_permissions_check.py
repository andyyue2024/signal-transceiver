"""
Test permission checking functionality.
"""
import sys
sys.path.insert(0, 'E:\\Workplace-Pycharm\\signal-transceiver')

def test_require_permissions():
    """Test that require_permissions creates PermissionChecker correctly."""
    from src.core.dependencies import require_permissions, PermissionChecker

    # Test single permission
    checker = require_permissions("data:read")
    assert isinstance(checker, PermissionChecker)
    assert checker.required_permissions == ["data:read"]

    # Test multiple permissions
    checker2 = require_permissions("data:read", "data:create")
    assert checker2.required_permissions == ["data:read", "data:create"]

    print("✓ require_permissions works correctly")


def test_api_imports():
    """Test that all API modules import correctly with permission checks."""
    from src.api.v1 import data, subscription, strategy, client, analytics, webhooks, compliance
    print("✓ All API modules imported successfully")


def test_permission_checker_class():
    """Test PermissionChecker class."""
    from src.core.dependencies import PermissionChecker

    checker = PermissionChecker(["data:read", "data:create"])
    assert hasattr(checker, '__call__')
    assert hasattr(checker, 'required_permissions')
    print("✓ PermissionChecker class works correctly")


if __name__ == "__main__":
    print("Testing permission checking functionality...")
    print()

    test_require_permissions()
    test_permission_checker_class()
    test_api_imports()

    print()
    print("=" * 50)
    print("All permission tests passed!")
