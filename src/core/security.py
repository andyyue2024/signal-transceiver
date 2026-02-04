"""
Security utilities for API Key generation and verification.
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Any

# Use bcrypt directly for Python 3.13 compatibility
bcrypt: Any = None
BCRYPT_AVAILABLE = False
try:
    import bcrypt as _bcrypt  # type: ignore
    bcrypt = _bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    import warnings
    warnings.warn("bcrypt not available, using fallback hashing")


def generate_api_key(prefix: str = "sk") -> Tuple[str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (api_key, hashed_key)
    """
    # Generate a random 32-byte key and encode as hex
    random_bytes = secrets.token_hex(32)
    api_key = f"{prefix}_{random_bytes}"

    # Hash the key for storage
    hashed_key = hash_api_key(api_key)

    return api_key, hashed_key


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_client_credentials() -> Tuple[str, str, str]:
    """
    Generate client credentials (client_key, client_secret, hashed_secret).

    Returns:
        Tuple of (client_key, client_secret, hashed_secret)
    """
    client_key = f"ck_{secrets.token_hex(16)}"
    client_secret = f"cs_{secrets.token_hex(32)}"
    hashed_secret = hash_api_key(client_secret)

    return client_key, client_secret, hashed_secret


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    else:
        # Fallback: SHA256 hash comparison (less secure, for testing only)
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if BCRYPT_AVAILABLE:
        # bcrypt requires password to be <= 72 bytes
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    else:
        # Fallback: SHA256 (less secure, for testing only)
        return hashlib.sha256(password.encode()).hexdigest()


def generate_token(length: int = 32) -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(length)


def calculate_expiry(days: int = 365) -> datetime:
    """Calculate expiry datetime from now."""
    return datetime.now(timezone.utc) + timedelta(days=days)


def is_expired(expiry_time: Optional[datetime]) -> bool:
    """Check if the given expiry time has passed."""
    if expiry_time is None:
        return False
    now = datetime.now(timezone.utc)
    # Make expiry_time timezone-aware if it's naive
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    return now > expiry_time
