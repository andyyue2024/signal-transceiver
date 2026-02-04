"""
IP Access Control - IP 访问控制
支持 IP 白名单和黑名单功能
"""
from typing import List, Optional, Set
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address

from src.config.database import Base


class IPWhitelist(Base):
    """IP 白名单"""
    __tablename__ = "ip_whitelist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 最长39字符
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class IPBlacklist(Base):
    """IP 黑名单"""
    __tablename__ = "ip_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 管理员ID
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class IPAccessControl:
    """IP 访问控制服务"""

    def __init__(self):
        # 内存缓存，避免频繁查询数据库
        self._whitelist_cache: Set[str] = set()
        self._blacklist_cache: Set[str] = set()
        self._cache_updated_at: Optional[datetime] = None
        self._cache_ttl = 300  # 5分钟缓存

    def is_valid_ip(self, ip: str) -> bool:
        """验证 IP 地址格式"""
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False

    def is_in_network(self, ip: str, network: str) -> bool:
        """检查 IP 是否在指定网络段内"""
        try:
            return ip_address(ip) in ip_network(network, strict=False)
        except ValueError:
            return False

    async def check_ip_blacklist(self, ip: str, db) -> bool:
        """
        检查 IP 是否在黑名单中

        Returns:
            True 如果在黑名单中（应拒绝访问）
            False 如果不在黑名单中（可以访问）
        """
        from sqlalchemy import select

        # 刷新缓存
        await self._refresh_cache(db)

        # 精确匹配
        if ip in self._blacklist_cache:
            return True

        # 检查数据库（支持网络段）
        result = await db.execute(
            select(IPBlacklist).where(
                IPBlacklist.is_active == True
            )
        )
        blacklist_entries = result.scalars().all()

        for entry in blacklist_entries:
            # 检查是否过期
            if entry.expires_at and entry.expires_at < datetime.utcnow():
                continue

            # 支持 CIDR 网络段
            if '/' in entry.ip_address:
                if self.is_in_network(ip, entry.ip_address):
                    return True
            elif entry.ip_address == ip:
                return True

        return False

    async def check_ip_whitelist(self, ip: str, user_id: int, db) -> bool:
        """
        检查 IP 是否在用户的白名单中

        Returns:
            True 如果在白名单中（可以访问）
            False 如果不在白名单中（应拒绝访问）
        """
        from sqlalchemy import select, and_

        # 如果没有启用白名单，默认允许
        result = await db.execute(
            select(IPWhitelist).where(
                and_(
                    IPWhitelist.user_id == user_id,
                    IPWhitelist.is_active == True
                )
            )
        )
        whitelist_entries = result.scalars().all()

        # 如果没有白名单配置，默认允许所有IP
        if not whitelist_entries:
            return True

        for entry in whitelist_entries:
            # 检查是否过期
            if entry.expires_at and entry.expires_at < datetime.utcnow():
                continue

            # 支持 CIDR 网络段
            if '/' in entry.ip_address:
                if self.is_in_network(ip, entry.ip_address):
                    return True
            elif entry.ip_address == ip:
                return True

        return False

    async def add_to_whitelist(
        self,
        ip: str,
        user_id: int,
        description: Optional[str],
        expires_at: Optional[datetime],
        db
    ) -> IPWhitelist:
        """添加 IP 到白名单"""
        if not self.is_valid_ip(ip.split('/')[0]):  # 验证 IP（忽略 CIDR）
            raise ValueError(f"Invalid IP address: {ip}")

        entry = IPWhitelist(
            user_id=user_id,
            ip_address=ip,
            description=description,
            is_active=True,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        # 清除缓存
        self._cache_updated_at = None

        return entry

    async def add_to_blacklist(
        self,
        ip: str,
        reason: Optional[str],
        created_by: Optional[int],
        expires_at: Optional[datetime],
        db
    ) -> IPBlacklist:
        """添加 IP 到黑名单"""
        if not self.is_valid_ip(ip.split('/')[0]):  # 验证 IP（忽略 CIDR）
            raise ValueError(f"Invalid IP address: {ip}")

        from sqlalchemy import select

        # 检查是否已存在
        result = await db.execute(
            select(IPBlacklist).where(IPBlacklist.ip_address == ip)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新现有记录
            existing.is_active = True
            existing.reason = reason
            existing.expires_at = expires_at
            existing.created_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            entry = existing
        else:
            # 创建新记录
            entry = IPBlacklist(
                ip_address=ip,
                reason=reason,
                created_by=created_by,
                is_active=True,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )
            db.add(entry)
            await db.commit()
            await db.refresh(entry)

        # 清除缓存
        self._cache_updated_at = None

        return entry

    async def remove_from_whitelist(self, ip: str, user_id: int, db) -> bool:
        """从白名单中移除 IP"""
        from sqlalchemy import select, and_

        result = await db.execute(
            select(IPWhitelist).where(
                and_(
                    IPWhitelist.ip_address == ip,
                    IPWhitelist.user_id == user_id
                )
            )
        )
        entry = result.scalar_one_or_none()

        if entry:
            entry.is_active = False
            await db.commit()
            self._cache_updated_at = None
            return True

        return False

    async def remove_from_blacklist(self, ip: str, db) -> bool:
        """从黑名单中移除 IP"""
        from sqlalchemy import select

        result = await db.execute(
            select(IPBlacklist).where(IPBlacklist.ip_address == ip)
        )
        entry = result.scalar_one_or_none()

        if entry:
            entry.is_active = False
            await db.commit()
            self._cache_updated_at = None
            return True

        return False

    async def get_user_whitelist(self, user_id: int, db) -> List[IPWhitelist]:
        """获取用户的白名单"""
        from sqlalchemy import select, and_

        result = await db.execute(
            select(IPWhitelist).where(
                and_(
                    IPWhitelist.user_id == user_id,
                    IPWhitelist.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def get_blacklist(self, db) -> List[IPBlacklist]:
        """获取所有黑名单"""
        from sqlalchemy import select

        result = await db.execute(
            select(IPBlacklist).where(IPBlacklist.is_active == True)
        )
        return result.scalars().all()

    async def _refresh_cache(self, db):
        """刷新缓存"""
        now = datetime.utcnow()

        # 检查缓存是否需要刷新
        if (self._cache_updated_at and
            (now - self._cache_updated_at).total_seconds() < self._cache_ttl):
            return

        from sqlalchemy import select

        # 刷新黑名单缓存
        result = await db.execute(
            select(IPBlacklist.ip_address).where(IPBlacklist.is_active == True)
        )
        self._blacklist_cache = set(result.scalars().all())

        self._cache_updated_at = now


# 全局实例
ip_access_control = IPAccessControl()
