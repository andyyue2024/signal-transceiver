"""
Tests for security module.
"""
import pytest
from datetime import datetime, timedelta

from src.core.security import (
    generate_api_key, hash_api_key, generate_client_credentials,
    verify_password, get_password_hash, generate_token,
    calculate_expiry, is_expired
)


class TestAPIKeyGeneration:
    """Tests for API key generation and hashing."""

    def test_generate_api_key_format(self):
        """Test API key format."""
        api_key, hashed = generate_api_key()

        assert api_key.startswith("sk_")
        assert len(api_key) == 67  # "sk_" + 64 hex chars
        assert len(hashed) == 64  # SHA256 hex

    def test_generate_api_key_with_custom_prefix(self):
        """Test API key with custom prefix."""
        api_key, _ = generate_api_key(prefix="test")

        assert api_key.startswith("test_")

    def test_generate_api_key_unique(self):
        """Test API keys are unique."""
        key1, _ = generate_api_key()
        key2, _ = generate_api_key()

        assert key1 != key2

    def test_hash_api_key_consistent(self):
        """Test hashing is consistent."""
        api_key = "test_key_12345"

        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)

        assert hash1 == hash2

    def test_hash_api_key_different_keys(self):
        """Test different keys produce different hashes."""
        hash1 = hash_api_key("key1")
        hash2 = hash_api_key("key2")

        assert hash1 != hash2


class TestClientCredentials:
    """Tests for client credentials generation."""

    def test_generate_client_credentials_format(self):
        """Test client credentials format."""
        client_key, client_secret, hashed = generate_client_credentials()

        assert client_key.startswith("ck_")
        assert client_secret.startswith("cs_")
        assert len(hashed) == 64

    def test_generate_client_credentials_unique(self):
        """Test credentials are unique."""
        key1, secret1, _ = generate_client_credentials()
        key2, secret2, _ = generate_client_credentials()

        assert key1 != key2
        assert secret1 != secret2


class TestPasswordHashing:
    """Tests for password hashing."""

    @pytest.mark.skip(reason="bcrypt compatibility issues with passlib in Python 3.13")
    def test_hash_password(self):
        """Test password hashing."""
        password = "secure_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    @pytest.mark.skip(reason="bcrypt compatibility issues with passlib in Python 3.13")
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "my_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    @pytest.mark.skip(reason="bcrypt compatibility issues with passlib in Python 3.13")
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "my_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False


class TestTokenGeneration:
    """Tests for token generation."""

    def test_generate_token_default_length(self):
        """Test token generation with default length."""
        token = generate_token()

        assert len(token) > 0

    def test_generate_token_custom_length(self):
        """Test token generation with custom length."""
        token = generate_token(length=64)

        assert len(token) > 0

    def test_generate_token_unique(self):
        """Test tokens are unique."""
        token1 = generate_token()
        token2 = generate_token()

        assert token1 != token2


class TestExpiry:
    """Tests for expiry utilities."""

    def test_calculate_expiry_default(self):
        """Test expiry calculation with default days."""
        from datetime import timezone
        expiry = calculate_expiry()
        now = datetime.now(timezone.utc)

        # Should be approximately 365 days from now
        diff = expiry - now
        assert 364 <= diff.days <= 365

    def test_calculate_expiry_custom_days(self):
        """Test expiry calculation with custom days."""
        from datetime import timezone
        expiry = calculate_expiry(days=30)
        now = datetime.now(timezone.utc)

        diff = expiry - now
        assert 29 <= diff.days <= 30

    def test_is_expired_not_expired(self):
        """Test is_expired for future date."""
        from datetime import timezone
        future = datetime.now(timezone.utc) + timedelta(days=1)

        assert is_expired(future) is False

    def test_is_expired_expired(self):
        """Test is_expired for past date."""
        from datetime import timezone
        past = datetime.now(timezone.utc) - timedelta(days=1)

        assert is_expired(past) is True

    def test_is_expired_none(self):
        """Test is_expired for None."""
        assert is_expired(None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
