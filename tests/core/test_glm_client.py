import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.core.glm_client import GLMClient, GLMClientConfig

class TestGLMClient:
    @pytest.fixture
    def config(self):
        return GLMClientConfig(
            api_key="test-api-key",
            model="glm-4-plus",
            timeout=10,
            max_retries=2
        )

    @pytest.fixture
    def mock_response(self):
        return {
            "choices": [{"message": {"content": "Test Response"}}],
            "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
        }

    @pytest.mark.asyncio
    async def test_ask_success(self, config, mock_response):
        client = GLMClient(config)
        
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_resp = Mock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = Mock()
            mock_post.return_value = mock_resp
            
            result = await client.ask("Hello GLM")
            
            assert result == "Test Response"
            mock_post.assert_called_once()
            
            # Verify request payload
            call_args = mock_post.call_args
            assert call_args[0][0] == "/chat/completions"
            payload = call_args[1]["json"]
            assert payload["model"] == "glm-4-plus"
            assert payload["messages"][0]["content"] == "Hello GLM"
        
        await client.close()

    @pytest.mark.asyncio
    async def test_ask_with_context(self, config, mock_response):
        client = GLMClient(config)
        
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_resp = Mock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = Mock()
            mock_post.return_value = mock_resp
            
            await client.ask("What is this?", context="You are a helpful assistant")
            
            payload = mock_post.call_args[1]["json"]
            messages = payload["messages"]
            
            # System message first, then user message
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
        
        await client.close()

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, config, mock_response):
        client = GLMClient(config)
        
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_resp = Mock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = Mock()
            mock_post.return_value = mock_resp
            
            await client.ask("Test")
            
            usage = client.get_token_usage()
            assert usage["total"] == 100
            assert usage["prompt"] == 50
            assert usage["completion"] == 50
        
        await client.close()

    @pytest.mark.asyncio
    async def test_get_stats(self, config, mock_response):
        client = GLMClient(config)
        
        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_resp = Mock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = Mock()
            mock_post.return_value = mock_resp
            
            await client.ask("Test 1")
            await client.ask("Test 2")
            
            stats = client.get_stats()
            assert stats["call_count"] == 2
            assert stats["model"] == "glm-4-plus"
        
        await client.close()
