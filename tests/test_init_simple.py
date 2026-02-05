#!/usr/bin/env python
"""
简单的初始化测试
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from src.config.database import Base
from src.core.security import get_password_hash, generate_api_key, generate_client_credentials
from src.models.user import User
from src.models.strategy import Strategy
from src.models.permission import Permission, Role, UserPermission
from datetime import datetime, timezone

async def test_init():
    print("=" * 60)
    print("🧪 测试数据库初始化")
    print("=" * 60)

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建成功")

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # 创建用户
        api_key, hashed_key = generate_api_key()
        ck, cs, hashed_cs = generate_client_credentials()
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            api_key=hashed_key,
            client_key=ck,
            client_secret=hashed_cs,
            is_active=True,
            is_admin=True
        )
        session.add(user)
        await session.flush()
        print(f"✅ 用户创建成功: {user.username} (ID: {user.id})")

        # 创建权限
        perm = Permission(
            name="创建数据",
            code="data:create",
            description="创建数据",
            resource="data",
            action="create"
        )
        session.add(perm)
        await session.flush()
        print(f"✅ 权限创建成功: {perm.code} (ID: {perm.id})")

        # 创建角色
        role = Role(
            name="管理员",
            code="admin",
            description="系统管理员",
            level=100,
            is_active=True
        )
        role.permissions = [perm]
        session.add(role)
        await session.flush()
        print(f"✅ 角色创建成功: {role.code} (ID: {role.id})")

        # 创建用户角色关联
        cp = UserPermission(
            user_id=user.id,
            role_id=role.id,
            is_active=True
        )
        session.add(cp)
        await session.flush()
        print(f"✅ 用户角色关联创建成功 (ID: {cp.id})")

        await session.commit()
        print("\n✅ 所有测试通过！初始化脚本应该可以正常工作")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_init())
