import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.file_ops import (
    glm_file_read, glm_file_create, glm_file_edit, 
    glm_file_delete, glm_file_rollback,
    FileReadParams, FileCreateParams, FileEditParams, 
    FileDeleteParams, FileRollbackParams
)
from src.core.sandbox import SandboxValidator
from src.core.backup import BackupManager
from src.models import ErrorCode

class TestFileOps:
    @pytest.fixture
    def setup_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
        
        validator = SandboxValidator(tmp_path)
        manager = BackupManager(tmp_path / ".glm_backups")
        
        with patch("src.tools.file_ops.get_sandbox_validator", return_value=validator), \
             patch("src.tools.file_ops.get_backup_manager", return_value=manager):
            yield validator, manager

    @pytest.mark.asyncio
    async def test_glm_file_read(self, setup_env, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello World", encoding="utf-8")
        
        params = FileReadParams(path=str(f))
        response = await glm_file_read(params)
        
        assert response.success is True
        assert response.data["content"] == "Hello World"

    @pytest.mark.asyncio
    async def test_glm_file_read_not_found(self, setup_env):
        params = FileReadParams(path="nonexistent.txt")
        response = await glm_file_read(params)
        
        assert response.success is False
        assert response.code == ErrorCode.FILE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_glm_file_read_sandbox_violation(self, setup_env):
        params = FileReadParams(path="../outside.txt")
        response = await glm_file_read(params)
        
        assert response.success is False
        assert response.code == ErrorCode.SANDBOX_VIOLATION

    @pytest.mark.asyncio
    async def test_glm_file_create(self, setup_env, tmp_path):
        target = tmp_path / "new.txt"
        params = FileCreateParams(path=str(target), content="New Content")
        
        response = await glm_file_create(params)
        
        assert response.success is True
        assert target.exists()
        assert target.read_text() == "New Content"

    @pytest.mark.asyncio
    async def test_glm_file_create_overwrite_deny(self, setup_env, tmp_path):
        target = tmp_path / "exist.txt"
        target.write_text("Old")
        
        params = FileCreateParams(path=str(target), content="New", overwrite=False)
        response = await glm_file_create(params)
        
        assert response.success is False
        assert response.code == ErrorCode.FILE_EXISTS
        assert target.read_text() == "Old"

    @pytest.mark.asyncio
    async def test_glm_file_edit(self, setup_env, tmp_path):
        target = tmp_path / "code.py"
        target.write_text("def foo():\n    pass")
        
        params = FileEditParams(
            path=str(target), 
            old_string="def foo():",
            new_string="def bar():"
        )
        
        response = await glm_file_edit(params)
        
        assert response.success is True
        assert target.read_text() == "def bar():\n    pass"
        assert "backup_path" in response.data

    @pytest.mark.asyncio
    async def test_glm_file_delete(self, setup_env, tmp_path):
        target = tmp_path / "todelete.txt"
        target.write_text("Bye")
        
        params = FileDeleteParams(path=str(target))
        response = await glm_file_delete(params)
        
        assert response.success is True
        assert not target.exists()
        assert "backup_path" in response.data
        # Verify backup exists
        assert Path(response.data["backup_path"]).exists()

    @pytest.mark.asyncio
    async def test_glm_file_rollback(self, setup_env, tmp_path):
        target = tmp_path / "data.txt"
        target.write_text("Version 1")
        
        # Manually create backup via manager or rely on edit/delete tools
        # Let's use internal manager for precision
        _, manager = setup_env
        await manager.create_backup(target)
        
        target.write_text("Version 2")
        
        params = FileRollbackParams(path=str(target), version=0) # Latest backup
        response = await glm_file_rollback(params)
        
        assert response.success is True
        assert target.read_text() == "Version 1"
