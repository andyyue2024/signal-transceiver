"""
Security utilities for API Key generation and verification.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    if USE_PASSLIB:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        return bcrypt_lib.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if USE_PASSLIB:
        return pwd_context.hash(password)
    else:
        return bcrypt_lib.hashpw(
            password.encode('utf-8'),
            bcrypt_lib.gensalt()
        ).decode('utf-8')


def generate_token(length: int = 32) -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(length)


def calculate_expiry(days: int = 365) -> datetime:
    """Calculate expiry datetime from now."""
    return datetime.utcnow() + timedelta(days=days)


def is_expired(expiry_time: Optional[datetime]) -> bool:
    """Check if the given expiry time has passed."""
    if expiry_time is None:
        return False
    return datetime.utcnow() > expiry_time
