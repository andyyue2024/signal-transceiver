"""
Database backup and restore service.
Provides automated backup, recovery, and retention management.
"""
import os
import shutil
import gzip
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from loguru import logger


@dataclass
class BackupInfo:
    """Information about a backup."""
    filename: str
    filepath: str
    size_bytes: int
    created_at: datetime
    backup_type: str  # 'full', 'incremental'
    database: str
    compressed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "size_human": self._human_size(self.size_bytes),
            "created_at": self.created_at.isoformat(),
            "backup_type": self.backup_type,
            "database": self.database,
            "compressed": self.compressed
        }

    @staticmethod
    def _human_size(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class BackupService:
    """Service for database backup and restore operations."""

    def __init__(
        self,
        backup_dir: str = "backups",
        retention_days: int = 30,
        max_backups: int = 50
    ):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.max_backups = max_backups

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(
        self,
        db_path: str,
        backup_type: str = "full",
        compress: bool = True
    ) -> BackupInfo:
        """
        Create a backup of the SQLite database.

        Args:
            db_path: Path to the database file
            backup_type: Type of backup ('full' or 'incremental')
            compress: Whether to compress the backup

        Returns:
            BackupInfo with details about the created backup
        """
        db_path = Path(db_path)

        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = db_path.stem
        ext = ".db.gz" if compress else ".db"
        backup_filename = f"{db_name}_{backup_type}_{timestamp}{ext}"
        backup_path = self.backup_dir / backup_filename

        try:
            if compress:
                # Create compressed backup
                with open(db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Simple copy
                shutil.copy2(db_path, backup_path)

            size = backup_path.stat().st_size

            backup_info = BackupInfo(
                filename=backup_filename,
                filepath=str(backup_path),
                size_bytes=size,
                created_at=datetime.now(),
                backup_type=backup_type,
                database=db_name,
                compressed=compress
            )

            # Save metadata
            await self._save_metadata(backup_info)

            logger.info(f"Backup created: {backup_filename} ({backup_info._human_size(size)})")

            # Cleanup old backups
            await self._cleanup_old_backups()

            return backup_info

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    async def restore_backup(
        self,
        backup_filename: str,
        target_path: str,
        overwrite: bool = False
    ) -> bool:
        """
        Restore a database from backup.

        Args:
            backup_filename: Name of the backup file
            target_path: Path where to restore the database
            overwrite: Whether to overwrite existing database

        Returns:
            True if restore was successful
        """
        backup_path = self.backup_dir / backup_filename
        target_path = Path(target_path)

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        if target_path.exists() and not overwrite:
            raise FileExistsError(f"Target exists and overwrite is False: {target_path}")

        try:
            # Create backup of current database before restore
            if target_path.exists():
                pre_restore_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(target_path, self.backup_dir / pre_restore_backup)
                logger.info(f"Created pre-restore backup: {pre_restore_backup}")

            # Restore from backup
            if backup_filename.endswith('.gz'):
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, target_path)

            logger.info(f"Database restored from: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise

    async def list_backups(
        self,
        database: Optional[str] = None,
        limit: int = 20
    ) -> List[BackupInfo]:
        """List available backups."""
        backups = []

        for filepath in sorted(self.backup_dir.glob("*.db*"), reverse=True):
            if filepath.suffix in ['.db', '.gz']:
                try:
                    stat = filepath.stat()
                    parts = filepath.stem.replace('.db', '').split('_')

                    db_name = parts[0] if parts else "unknown"
                    backup_type = parts[1] if len(parts) > 1 else "full"

                    if database and db_name != database:
                        continue

                    backup_info = BackupInfo(
                        filename=filepath.name,
                        filepath=str(filepath),
                        size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_mtime),
                        backup_type=backup_type,
                        database=db_name,
                        compressed=filepath.name.endswith('.gz')
                    )
                    backups.append(backup_info)

                    if len(backups) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Error reading backup {filepath}: {e}")

        return backups

    async def delete_backup(self, backup_filename: str) -> bool:
        """Delete a specific backup."""
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            return False

        try:
            backup_path.unlink()

            # Remove metadata
            meta_path = self.backup_dir / f"{backup_filename}.meta"
            if meta_path.exists():
                meta_path.unlink()

            logger.info(f"Backup deleted: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    async def get_backup_info(self, backup_filename: str) -> Optional[BackupInfo]:
        """Get information about a specific backup."""
        backups = await self.list_backups()
        for backup in backups:
            if backup.filename == backup_filename:
                return backup
        return None

    async def _save_metadata(self, backup_info: BackupInfo):
        """Save backup metadata to file."""
        meta_path = self.backup_dir / f"{backup_info.filename}.meta"
        with open(meta_path, 'w') as f:
            json.dump(backup_info.to_dict(), f, indent=2)

    async def _cleanup_old_backups(self):
        """Remove old backups based on retention policy."""
        backups = await self.list_backups(limit=1000)

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        for backup in backups:
            # Remove by age
            if backup.created_at < cutoff_date:
                await self.delete_backup(backup.filename)
                removed_count += 1

        # Remove by count (keep only max_backups)
        if len(backups) > self.max_backups:
            for backup in backups[self.max_backups:]:
                await self.delete_backup(backup.filename)
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backups")

    def get_stats(self) -> Dict[str, Any]:
        """Get backup statistics."""
        total_size = 0
        backup_count = 0
        oldest = None
        newest = None

        for filepath in self.backup_dir.glob("*.db*"):
            if filepath.suffix in ['.db', '.gz']:
                stat = filepath.stat()
                total_size += stat.st_size
                backup_count += 1

                mtime = datetime.fromtimestamp(stat.st_mtime)
                if oldest is None or mtime < oldest:
                    oldest = mtime
                if newest is None or mtime > newest:
                    newest = mtime

        return {
            "backup_count": backup_count,
            "total_size_bytes": total_size,
            "total_size_human": BackupInfo._human_size(total_size),
            "oldest_backup": oldest.isoformat() if oldest else None,
            "newest_backup": newest.isoformat() if newest else None,
            "retention_days": self.retention_days,
            "max_backups": self.max_backups,
            "backup_dir": str(self.backup_dir)
        }


# Global backup service instance
backup_service = BackupService()
