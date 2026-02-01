import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.core.glm_executor import GLMExecutor
from src.core.glm_client import GLMClient, GLMClientConfig

class TestGLMExecutor:
    @pytest.fixture
    def mock_client(self):
        client = Mock(spec=GLMClient)
        client.ask = AsyncMock(return_value="Test Response")
        client.check_api = AsyncMock(return_value=True)
        client.get_stats = Mock(return_value={
            "call_count": 1,
            "model": "glm-4-plus",
            "total": 100,
            "prompt": 50,
            "completion": 50,
            "base_url": "https://open.bigmodel.cn/api/paas/v4"
        })
        client.close = AsyncMock()
        return client

    @pytest.fixture
    def executor(self, mock_client):
        return GLMExecutor(client=mock_client)

    @pytest.mark.asyncio
    async def test_execute(self, executor, mock_client):
        result = await executor.execute("Do something")
        
        assert result == "Test Response"
        mock_client.ask.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_context(self, executor, mock_client):
        await executor.execute(
            prompt="Analyze this",
            context="Some code here",
            working_dir="/workspace/project"
        )
        
        # Verify the context was assembled correctly
        call_args = mock_client.ask.call_args
        assert call_args[1]["task"] == "Analyze this"
        assert "작업 디렉토리: /workspace/project" in call_args[1]["context"]
        assert "Some code here" in call_args[1]["context"]

    @pytest.mark.asyncio
    async def test_check_api(self, executor, mock_client):
        result = await executor.check_api()
        assert result is True
        mock_client.check_api.assert_called_once()

    def test_get_stats(self, executor, mock_client):
        stats = executor.get_stats()
        assert stats["call_count"] == 1
        assert stats["model"] == "glm-4-plus"

    @pytest.mark.asyncio
    async def test_close(self, executor, mock_client):
        await executor.close()
        mock_client.close.assert_called_once()
