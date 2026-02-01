import pytest
from pathlib import Path
from unittest.mock import patch

from src.tools.memory_ops import (
    glm_memory_save, glm_memory_get, glm_memory_list, glm_memory_delete,
    MemorySaveParams, MemoryGetParams, MemoryListParams, MemoryDeleteParams
)
from src.models import ErrorCode

class TestMemoryOps:
    @pytest.fixture
    def setup_memory(self, tmp_path):
        memory_dir = tmp_path / "memory"
        with patch("src.tools.memory_ops.MEMORY_DIR", memory_dir):
            yield memory_dir

    @pytest.mark.asyncio
    async def test_memory_save_and_get(self, setup_memory):
        # Save
        save_params = MemorySaveParams(key="test_key", value="test_value", category="general")
        resp = await glm_memory_save(save_params)
        assert resp.success is True

        # Get
        get_params = MemoryGetParams(key="test_key", category="general")
        resp = await glm_memory_get(get_params)
        assert resp.success is True
        assert resp.data["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_memory_get_cross_category(self, setup_memory):
        # Save to specific category
        await glm_memory_save(MemorySaveParams(key="my_key", value="val", category="code"))
        
        # Get without category (should search default categories)
        resp = await glm_memory_get(MemoryGetParams(key="my_key"))
        assert resp.success is True
        assert resp.data["value"] == "val"

    @pytest.mark.asyncio
    async def test_memory_list(self, setup_memory):
        await glm_memory_save(MemorySaveParams(key="k1", value="v1", category="general"))
        await glm_memory_save(MemorySaveParams(key="k2", value="v2", category="code"))

        # List all
        resp = await glm_memory_list(MemoryListParams(limit=10))
        assert resp.success is True
        assert resp.data["total"] == 2
        
        # List specific category
        resp = await glm_memory_list(MemoryListParams(category="general"))
        assert resp.success is True
        assert resp.data["total"] == 1
        assert resp.data["entries"][0]["key"] == "k1"

    @pytest.mark.asyncio
    async def test_memory_delete(self, setup_memory):
        await glm_memory_save(MemorySaveParams(key="del_key", value="del_val"))
        
        resp = await glm_memory_delete(MemoryDeleteParams(key="del_key"))
        assert resp.success is True
        
        # Verify gone
        resp = await glm_memory_get(MemoryGetParams(key="del_key"))
        assert resp.success is False
        assert resp.code == ErrorCode.FILE_NOT_FOUND
