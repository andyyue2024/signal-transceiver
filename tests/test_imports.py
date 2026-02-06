#!/usr/bin/env python3
"""Test imports to verify code changes are correct."""
import sys
sys.path.insert(0, '..')

print("Testing imports...")

try:
    from src.services.data_service import DataService
    print("✓ DataService imported")
except Exception as e:
    print(f"✗ DataService import failed: {e}")

try:
    from src.services.subscription_service import SubscriptionService
    print("✓ SubscriptionService imported")
except Exception as e:
    print(f"✗ SubscriptionService import failed: {e}")

try:
    from src.schemas.data import DataResponse, DataCreate
    print("✓ Data schemas imported")
except Exception as e:
    print(f"✗ Data schemas import failed: {e}")

try:
    from src.schemas.subscription import SubscriptionResponse, SubscriptionCreate
    print("✓ Subscription schemas imported")
except Exception as e:
    print(f"✗ Subscription schemas import failed: {e}")

try:
    from src.api.v1.subscription import router
    print("✓ Subscription router imported")
except Exception as e:
    print(f"✗ Subscription router import failed: {e}")

try:
    from src.api.v1.data import router
    print("✓ Data router imported")
except Exception as e:
    print(f"✗ Data router import failed: {e}")

try:
    from src.main import app
    print("✓ Main app imported")
except Exception as e:
    print(f"✗ Main app import failed: {e}")

print("\nAll imports complete!")
