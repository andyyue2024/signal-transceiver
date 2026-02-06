#!/usr/bin/env python3
"""
Quick verification test for the demo fixes.
Run this after starting the server on port 8000.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx


BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            print(f"✓ Health check: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Version: {data.get('version')}")
                return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
    return False


async def test_login():
    """Test login endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_V1}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10.0
            )
            print(f"✓ Login: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                api_key = data.get("data", {}).get("api_key")
                print(f"  API Key: {api_key[:30]}..." if api_key else "  No API key")
                return api_key
        except Exception as e:
            print(f"✗ Login failed: {e}")
    return None


async def test_data_upload(client_key: str, client_secret: str):
    """Test data upload endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_V1}/data",
                headers={
                    "X-Client-Key": client_key,
                    "X-Client-Secret": client_secret
                },
                json={
                    "type": "test_signal",
                    "symbol": "TEST",
                    "execute_date": "2026-02-06",
                    "description": "Test data upload",
                    "payload": {"test": True},
                    "strategy_id": "strategy_s_remote"
                },
                timeout=10.0
            )
            print(f"✓ Data upload: {response.status_code}")
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Data upload failed: {e}")
    return False


async def test_subscription_create(client_key: str, client_secret: str):
    """Test subscription creation."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_V1}/subscriptions",
                headers={
                    "X-Client-Key": client_key,
                    "X-Client-Secret": client_secret
                },
                json={
                    "name": "Test Subscription",
                    "strategy_id": "strategy_s_remote",
                    "subscription_type": "polling"
                },
                timeout=10.0
            )
            print(f"✓ Subscription create: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                return data.get("id")
            else:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Subscription create failed: {e}")
    return None


async def test_poll_endpoint(subscription_id: int, client_key: str, client_secret: str):
    """Test poll endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_V1}/subscriptions/{subscription_id}/poll",
                headers={
                    "X-Client-Key": client_key,
                    "X-Client-Secret": client_secret
                },
                timeout=10.0
            )
            print(f"✓ Poll endpoint: {response.status_code}")
            if response.status_code == 200:
                return True
            else:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Poll endpoint failed: {e}")
    return False


def load_credentials():
    """Load client credentials from init_credentials.txt."""
    creds_file = os.path.join(os.path.dirname(__file__), "init_credentials.txt")
    credentials = {}

    if not os.path.exists(creds_file):
        print(f"Warning: Credentials file not found: {creds_file}")
        return credentials

    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            content = f.read()

        current_user = None
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.endswith(':') and not line.startswith(' ') and not stripped.startswith('Client'):
                current_user = stripped[:-1]
                credentials[current_user] = {}
            elif current_user and 'Client Key:' in stripped:
                credentials[current_user]['client_key'] = stripped.split(':', 1)[1].strip()
            elif current_user and 'Client Secret:' in stripped:
                credentials[current_user]['client_secret'] = stripped.split(':', 1)[1].strip()
    except Exception as e:
        print(f"Warning: Failed to load credentials: {e}")

    return credentials


async def main():
    print("=" * 60)
    print("Signal Transceiver - Quick Verification Test")
    print("=" * 60)
    print()

    # Check server
    print("1. Testing health endpoint...")
    if not await test_health():
        print("\n✗ Server is not running. Start it with:")
        print("  uvicorn src.main:app --host 0.0.0.0 --port 8000")
        return 1
    print()

    # Login
    print("2. Testing login...")
    api_key = await test_login()
    if not api_key:
        print("\n✗ Login failed")
        return 1
    print()

    # Load credentials
    print("3. Loading client credentials...")
    credentials = load_credentials()
    trader_creds = credentials.get("trader1", {})
    client_key = trader_creds.get("client_key")
    client_secret = trader_creds.get("client_secret")

    if not client_key or not client_secret:
        print("✗ Could not load trader1 credentials")
        print("  Run 'python src/init_db.py' to initialize the database")
        return 1
    print(f"✓ Loaded credentials for trader1")
    print()

    # Test data upload
    print("4. Testing data upload...")
    upload_ok = await test_data_upload(client_key, client_secret)
    print()

    # Test subscription
    print("5. Testing subscription creation...")
    sub_id = await test_subscription_create(client_key, client_secret)
    print()

    # Test poll
    if sub_id:
        print("6. Testing poll endpoint...")
        await test_poll_endpoint(sub_id, client_key, client_secret)
        print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
