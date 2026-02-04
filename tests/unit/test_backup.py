"""
Tests for backup service.
"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.services.backup_service import BackupService, BackupInfo


class TestBackupService:
    """Tests for backup service."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def test_db(self, temp_dir):
        """Create a test database file."""
        db_path = Path(temp_dir) / "test.db"
        db_path.write_text("test database content")
        return str(db_path)

    @pytest.fixture
    def backup_service(self, temp_dir):
        """Create backup service with temp directory."""
        backup_dir = Path(temp_dir) / "backups"
        return BackupService(
            backup_dir=str(backup_dir),
            retention_days=7,
            max_backups=5
        )

    @pytest.mark.asyncio
    async def test_create_backup(self, backup_service, test_db):
        """Test creating a backup."""
        backup = await backup_service.create_backup(test_db, compress=False)

        assert backup.filename is not None
        assert backup.size_bytes > 0
        assert backup.backup_type == "full"
        assert backup.compressed is False
        assert os.path.exists(backup.filepath)

    @pytest.mark.asyncio
    async def test_create_backup_compressed(self, backup_service, test_db):
        """Test creating a compressed backup."""
        backup = await backup_service.create_backup(test_db, compress=True)

        assert backup.filename.endswith(".gz")
        assert backup.compressed is True

    @pytest.mark.asyncio
    async def test_list_backups(self, backup_service, test_db):
        """Test listing backups."""
        # Create a few backups
        await backup_service.create_backup(test_db, compress=False)
        await backup_service.create_backup(test_db, compress=False)

        backups = await backup_service.list_backups()

        assert len(backups) >= 2

    @pytest.mark.asyncio
    async def test_delete_backup(self, backup_service, test_db):
        """Test deleting a backup."""
        backup = await backup_service.create_backup(test_db, compress=False)

        deleted = await backup_service.delete_backup(backup.filename)

        assert deleted is True
        assert not os.path.exists(backup.filepath)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_backup(self, backup_service):
        """Test deleting a nonexistent backup."""
        deleted = await backup_service.delete_backup("nonexistent.db")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_restore_backup(self, backup_service, test_db, temp_dir):
        """Test restoring a backup."""
        # Create backup
        backup = await backup_service.create_backup(test_db, compress=False)

        # Modify original
        with open(test_db, 'w') as f:
            f.write("modified content")

        # Restore
        restore_path = Path(temp_dir) / "restored.db"
        await backup_service.restore_backup(backup.filename, str(restore_path))

        # Verify restore
        assert restore_path.exists()
        assert restore_path.read_text() == "test database content"

    @pytest.mark.asyncio
    async def test_restore_compressed_backup(self, backup_service, test_db, temp_dir):
        """Test restoring a compressed backup."""
        backup = await backup_service.create_backup(test_db, compress=True)

        restore_path = Path(temp_dir) / "restored.db"
        await backup_service.restore_backup(backup.filename, str(restore_path))

        assert restore_path.exists()

    @pytest.mark.asyncio
    async def test_backup_not_found_error(self, backup_service):
        """Test backup with non-existent database."""
        with pytest.raises(FileNotFoundError):
            await backup_service.create_backup("/nonexistent/db.db")

    def test_get_stats(self, backup_service):
        """Test getting backup stats."""
        stats = backup_service.get_stats()

        assert "backup_count" in stats
        assert "total_size_bytes" in stats
        assert "retention_days" in stats
        assert "max_backups" in stats


class TestBackupInfo:
    """Tests for BackupInfo dataclass."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        info = BackupInfo(
            filename="test.db",
            filepath="/path/test.db",
            size_bytes=1024,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            backup_type="full",
            database="test",
            compressed=False
        )

        d = info.to_dict()

        assert d["filename"] == "test.db"
        assert d["size_bytes"] == 1024
        assert d["size_human"] == "1024.0 B"
        assert d["backup_type"] == "full"

    def test_human_size_kb(self):
        """Test human readable size in KB."""
        info = BackupInfo(
            filename="test.db",
            filepath="/path/test.db",
            size_bytes=2048,
            created_at=datetime.now(),
            backup_type="full",
            database="test",
            compressed=False
        )

        d = info.to_dict()
        assert "KB" in d["size_human"]

    def test_human_size_mb(self):
        """Test human readable size in MB."""
        info = BackupInfo(
            filename="test.db",
            filepath="/path/test.db",
            size_bytes=2 * 1024 * 1024,
            created_at=datetime.now(),
            backup_type="full",
            database="test",
            compressed=False
        )

        d = info.to_dict()
        assert "MB" in d["size_human"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
