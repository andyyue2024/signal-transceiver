#!/usr/bin/env python
"""
初始化管理员用户脚本
创建默认的管理员账号用于首次登录
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config.database import Base
from src.config.settings import settings
from src.models.user import User
from src.core.security import get_password_hash, generate_api_key, generate_client_credentials


async def init_admin_user():
    """初始化管理员用户"""
    print("=" * 80)
    print("🔐 Signal Transceiver - 初始化管理员用户")
    print("=" * 80)

    # 创建数据库引擎
    engine = create_async_engine(
        settings.database_url,
        echo=False
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # 检查是否已存在管理员
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("\n⚠️  管理员用户已存在！")
            print(f"   用户名: admin")

            # 询问是否重置密码
            reset = input("\n是否重置管理员密码? (yes/no): ").lower()
            if reset == 'yes':
                new_password = input("请输入新密码: ")
                if len(new_password) < 6:
                    print("❌ 密码长度至少为6位！")
                    return

                existing_admin.hashed_password = get_password_hash(new_password)
                await session.commit()
                print(f"\n✅ 管理员密码已重置！")
                print(f"   用户名: admin")
                print(f"   新密码: {new_password}")
            else:
                print("\n❌ 操作已取消")
            return

        # 创建新的管理员用户
        print("\n📝 创建新的管理员用户...")

        # 生成凭证
        api_key, hashed_key = generate_api_key()
        client_key, client_secret, hashed_secret = generate_client_credentials()

        # 默认密码
        default_password = "admin123"

        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash(default_password),
            api_key=hashed_key,
            client_key=client_key,
            client_secret=hashed_secret,
            is_active=True,
            is_admin=True,
            full_name="系统管理员"
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("\n" + "=" * 80)
        print("✅ 管理员用户创建成功！")
        print("=" * 80)
        print(f"\n📋 登录信息:")
        print(f"   登录地址: http://localhost:8000/admin/login")
        print(f"   用户名: admin")
        print(f"   密码: {default_password}")
        print(f"\n🔑 API 凭证:")
        print(f"   API Key: {api_key}")
        print(f"   Client Key: {client_key}")
        print(f"   Client Secret: {client_secret}")
        print("\n" + "=" * 80)
        print("⚠️  重要提示:")
        print("   1. 请立即修改默认密码！")
        print("   2. 请妥善保管 API 凭证！")
        print("   3. 建议在生产环境使用强密码！")
        print("=" * 80)

        # 保存到文件
        with open("admin_credentials.txt", "w", encoding="utf-8") as f:
            f.write("Signal Transceiver - 管理员凭证\n")
            f.write("=" * 80 + "\n")
            f.write(f"登录地址: http://localhost:8000/admin/login\n")
            f.write(f"用户名: admin\n")
            f.write(f"密码: {default_password}\n")
            f.write(f"\nAPI Key: {api_key}\n")
            f.write(f"Client Key: {client_key}\n")
            f.write(f"Client Secret: {client_secret}\n")
            f.write("\n⚠️ 请立即修改默认密码并妥善保管此文件！\n")

        print("\n💾 凭证已保存到: admin_credentials.txt")
        print("   请妥善保管此文件，并在生产环境删除！")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(init_admin_user())
        print("\n🎉 初始化完成！")
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
