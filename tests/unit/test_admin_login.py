"""
Tests for Admin Login and CRUD UI features.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestAdminLogin:
    """Test admin login page."""

    def test_admin_login_page_loads(self):
        """Test that login page loads successfully."""
        response = client.get("/admin/login")
        assert response.status_code == 200
        assert "Signal Transceiver" in response.text

    def test_login_page_has_form(self):
        """Test that login page contains form elements."""
        response = client.get("/admin/login")
        assert '<form id="loginForm"' in response.text
        assert 'id="username"' in response.text
        assert 'id="password"' in response.text

    def test_login_page_glassmorphism(self):
        """Test that login page has glassmorphism effects."""
        response = client.get("/admin/login")
        assert "backdrop-filter" in response.text
        assert "rgba(255, 255, 255, 0.25)" in response.text

    def test_logout_page(self):
        """Test logout endpoint."""
        response = client.get("/admin/logout")
        assert response.status_code == 200
        assert "localStorage.removeItem" in response.text


class TestAdminUICRUD:
    """Test Admin UI CRUD features."""

    def test_admin_ui_user_crud(self):
        """Test user CRUD interface."""
        response = client.get("/admin/ui")
        assert response.status_code == 200
        assert "showCreateUser" in response.text
        assert "createUserModal" in response.text
        assert "newUsername" in response.text

    def test_admin_ui_client_crud(self):
        """Test client CRUD interface."""
        response = client.get("/admin/ui")
        assert "createClient(" in response.text
        assert "createClientModal" in response.text
        assert "newClientName" in response.text

    def test_admin_ui_strategy_crud(self):
        """Test strategy CRUD interface."""
        response = client.get("/admin/ui")
        assert "createStrategy(" in response.text
        assert "createStrategyModal" in response.text
        assert "newStrategyId" in response.text

    def test_admin_ui_role_management(self):
        """Test role management interface."""
        response = client.get("/admin/ui")
        assert "assignRoleToClient" in response.text
        assert "createRole" in response.text
        assert "newRoleCode" in response.text

    def test_admin_ui_permission_management(self):
        """Test permission management interface."""
        response = client.get("/admin/ui")
        assert "createPermission" in response.text
        assert "createPermModal" in response.text
        assert "newPermCode" in response.text

    def test_admin_ui_has_all_modals(self):
        """Test that all CRUD modals exist."""
        response = client.get("/admin/ui")
        modals = [
            "createUserModal",
            "createClientModal",
            "createStrategyModal",
            "createRoleModal",
            "createPermModal"
        ]
        for modal in modals:
            assert modal in response.text


class TestAdminUIFunctions:
    """Test JavaScript functions in Admin UI."""

    def test_crud_functions_exist(self):
        """Test that all CRUD JavaScript functions exist."""
        response = client.get("/admin/ui")
        functions = [
            "loadUsers()",
            "showCreateUser()",
            "createUser()",
            "showCreateClient()",
            "createClient()",
            "showCreateStrategy()",
            "createStrategy()",
            "showCreateRole()",
            "createRole()",
            "showCreatePermission()",
            "createPermission()",
            "assignRoleToClient()"
        ]
        for func in functions:
            assert func in response.text

    def test_hide_functions_exist(self):
        """Test that hide modal functions exist."""
        response = client.get("/admin/ui")
        hide_functions = [
            "hideCreateUser()",
            "hideCreateClient()",
            "hideCreateStrategy()",
            "hideCreateRole()",
            "hideCreatePermission()"
        ]
        for func in hide_functions:
            assert func in response.text
