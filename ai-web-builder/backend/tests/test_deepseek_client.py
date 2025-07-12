"""
Tests for DeepSeek API client
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from ai.clients.deepseek import DeepSeekClient, DeepSeekError
from ai.models import AIRequest, TaskType, UserTier

@pytest.mark.asyncio
async def test_deepseek_client_initialization():
    """Test DeepSeek client initialization"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-api-key"
        
        client = DeepSeekClient()
        assert client.api_key == "test-api-key"

def test_deepseek_client_missing_api_key():
    """Test DeepSeek client fails without API key"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = None
        
        with pytest.raises(ValueError, match="DeepSeek API key is required"):
            DeepSeekClient()

def test_system_prompt_generation():
    """Test system prompt generation for different task types"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        client = DeepSeekClient()
        
        # Test code generation prompt
        code_prompt = client._get_system_prompt("code_generation")
        assert "React" in code_prompt
        assert "TypeScript" in code_prompt
        
        # Test analysis prompt
        analysis_prompt = client._get_system_prompt("analysis")
        assert "analyst" in analysis_prompt.lower()
        assert "insights" in analysis_prompt.lower()

def test_payload_preparation():
    """Test API payload preparation"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        client = DeepSeekClient()
        
        request = AIRequest(
            task_type=TaskType.CODE_GENERATION.value,
            complexity=3,
            content="Create a button component",
            user_tier=UserTier.CREATOR.value
        )
        
        payload = client._prepare_payload(request, temperature=0.7, max_tokens=1000)
        
        assert payload["model"] == "deepseek-coder"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 1000
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Create a button component"

def test_quality_assessment():
    """Test response quality assessment"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        client = DeepSeekClient()
        
        # Test code response
        code_response = """
        import React from 'react';
        
        export const Button = () => {
          return <button>Click me</button>;
        };
        """
        
        quality = client._assess_response_quality(code_response, "code_generation")
        assert quality > 0.8  # Should be high quality for good code
        
        # Test poor response
        poor_response = "ok"
        poor_quality = client._assess_response_quality(poor_response, "code_generation")
        assert poor_quality < 0.5  # Should be low quality

@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        client = DeepSeekClient()
        
        cost_estimate = await client.estimate_cost(
            "Create a React component with TypeScript",
            "code_generation"
        )
        
        assert "estimated_input_tokens" in cost_estimate
        assert "estimated_output_tokens" in cost_estimate
        assert "estimated_cost" in cost_estimate
        assert "model" in cost_estimate
        assert cost_estimate["estimated_cost"] > 0
        assert cost_estimate["model"] == "deepseek-v3"

@pytest.mark.asyncio
async def test_connection_test_success():
    """Test successful connection test"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        client = DeepSeekClient()
        
        # Mock successful API response
        mock_response = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        
        with patch.object(client, 'generate_completion') as mock_generate:
            from ai.models import AIResponse, ModelType
            mock_generate.return_value = AIResponse(
                content="Hello!",
                model_used=ModelType.DEEPSEEK_V3,
                input_tokens=10,
                output_tokens=5,
                cost=0.001,
                processing_time=1.5
            )
            
            result = await client.test_connection()
            
            assert result["success"] is True
            assert result["model"] == "deepseek-coder"
            assert "response_time" in result
            assert "cost" in result

@pytest.mark.asyncio
async def test_connection_test_failure():
    """Test failed connection test"""
    with patch('ai.clients.deepseek.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "invalid-key"
        
        client = DeepSeekClient()
        
        with patch.object(client, 'generate_completion') as mock_generate:
            mock_generate.side_effect = DeepSeekError("Invalid API key")
            
            result = await client.test_connection()
            
            assert result["success"] is False
            assert "error" in result
            assert result["error_type"] == "DeepSeekError"