"""
Tests for Google Gemini API client
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from ai.clients.gemini import GeminiClient, GeminiError
from ai.models import AIRequest, TaskType, UserTier, ModelType

@pytest.mark.asyncio
async def test_gemini_client_initialization():
    """Test Gemini client initialization"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-api-key"
        
        client = GeminiClient()
        assert client.api_key == "test-api-key"

def test_gemini_client_missing_api_key():
    """Test Gemini client fails without API key"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = None
        
        with pytest.raises(ValueError, match="Gemini API key is required"):
            GeminiClient()

def test_system_context_generation():
    """Test system context generation for different task types"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Test code generation context
        code_context = client._get_system_context("code_generation")
        assert "React" in code_context
        assert "TypeScript" in code_context
        assert "Tailwind" in code_context
        
        # Test content writing context
        content_context = client._get_system_context("content_writing")
        assert "content writer" in content_context.lower()
        assert "engaging" in content_context.lower()
        
        # Test analysis context
        analysis_context = client._get_system_context("analysis")
        assert "analyst" in analysis_context.lower()
        assert "recommendations" in analysis_context.lower()

def test_optimized_prompt_creation():
    """Test optimized prompt creation"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        request = AIRequest(
            task_type=TaskType.CODE_GENERATION.value,
            complexity=3,
            content="Create a React button component",
            user_tier=UserTier.CREATOR.value
        )
        
        prompt = client._create_optimized_prompt(request)
        
        assert "React" in prompt
        assert "TypeScript" in prompt
        assert "Create a React button component" in prompt
        assert "User Request:" in prompt

def test_payload_preparation():
    """Test API payload preparation"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        request = AIRequest(
            task_type=TaskType.CONTENT_WRITING.value,
            complexity=4,
            content="Write a blog post about AI",
            user_tier=UserTier.BUSINESS.value
        )
        
        payload = client._prepare_payload(request, temperature=0.8, max_tokens=2000)
        
        assert "contents" in payload
        assert "generationConfig" in payload
        assert "safetySettings" in payload
        
        # Check generation config
        gen_config = payload["generationConfig"]
        assert gen_config["temperature"] == 0.8
        assert gen_config["maxOutputTokens"] == 2000
        
        # Check contents structure
        contents = payload["contents"]
        assert len(contents) == 1
        assert "parts" in contents[0]
        assert len(contents[0]["parts"]) == 1
        assert "text" in contents[0]["parts"][0]

def test_quality_assessment():
    """Test response quality assessment"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Test good code response
        code_response = """
        import React from 'react';
        
        interface ButtonProps {
          children: React.ReactNode;
          onClick: () => void;
          className?: string;
        }
        
        export const Button: React.FC<ButtonProps> = ({ children, onClick, className }) => {
          return (
            <button 
              onClick={onClick}
              className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${className}`}
            >
              {children}
            </button>
          );
        };
        """
        
        quality = client._assess_response_quality(code_response, "code_generation")
        assert quality > 0.85  # Should be high quality for good code
        
        # Test content writing response
        content_response = """
        # The Future of AI in Web Development
        
        Artificial Intelligence is transforming how we build web applications. Here are the key trends:
        
        ## 1. Automated Code Generation
        AI tools can now generate production-ready code...
        
        ## 2. Intelligent Design Systems
        Modern AI can create responsive designs...
        
        ## Conclusion
        The integration of AI in web development is accelerating innovation.
        """
        
        content_quality = client._assess_response_quality(content_response, "content_writing")
        assert content_quality > 0.8  # Should be high quality for well-structured content
        
        # Test poor response
        poor_response = "ok sure"
        poor_quality = client._assess_response_quality(poor_response, "analysis")
        assert poor_quality < 0.5  # Should be low quality

@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation for different models"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Test Flash model estimation
        flash_estimate = await client.estimate_cost(
            "Create a React component with TypeScript and Tailwind CSS",
            "code_generation",
            "gemini-1.5-flash"
        )
        
        assert "estimated_input_tokens" in flash_estimate
        assert "estimated_output_tokens" in flash_estimate
        assert "estimated_cost" in flash_estimate
        assert flash_estimate["model"] == "gemini-1.5-flash"
        assert flash_estimate["model_type"] == "gemini-1.5-flash"
        assert flash_estimate["estimated_cost"] > 0
        
        # Test Pro model estimation
        pro_estimate = await client.estimate_cost(
            "Create a React component with TypeScript and Tailwind CSS",
            "code_generation", 
            "gemini-1.5-pro"
        )
        
        assert pro_estimate["model"] == "gemini-1.5-pro"
        assert pro_estimate["model_type"] == "gemini-1.5-pro"
        # Pro should be more expensive than Flash
        assert pro_estimate["estimated_cost"] > flash_estimate["estimated_cost"]

@pytest.mark.asyncio 
async def test_connection_test_success():
    """Test successful connection test"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Mock successful response
        with patch.object(client, 'generate_completion') as mock_generate:
            from ai.models import AIResponse, ModelType
            mock_generate.return_value = AIResponse(
                content="Hello! I'm Google's Gemini AI assistant.",
                model_used=ModelType.GEMINI_FLASH,
                input_tokens=15,
                output_tokens=10,
                cost=0.0002,
                processing_time=1.2
            )
            
            result = await client.test_connection()
            
            assert result["success"] is True
            assert result["model"] == "gemini-1.5-flash"
            assert "response_time" in result
            assert "cost" in result
            assert "content_preview" in result

@pytest.mark.asyncio
async def test_connection_test_failure():
    """Test failed connection test"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "invalid-key"
        
        client = GeminiClient()
        
        with patch.object(client, 'generate_completion') as mock_generate:
            mock_generate.side_effect = GeminiError("Invalid API key")
            
            result = await client.test_connection()
            
            assert result["success"] is False
            assert "error" in result
            assert result["error_type"] == "GeminiError"

def test_response_parsing():
    """Test response parsing from Gemini API"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Mock API response
        api_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Here's a React component for you:\n\nconst Button = () => <button>Click me</button>;"}
                        ]
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 20,
                "candidatesTokenCount": 15
            }
        }
        
        request = AIRequest(
            task_type="code_generation",
            complexity=3,
            content="Create a button",
            user_tier="creator"
        )
        
        from datetime import datetime
        start_time = datetime.utcnow()
        
        response = client._parse_response(api_response, request, ModelType.GEMINI_FLASH, start_time)
        
        assert response.content.startswith("Here's a React component")
        assert response.model_used == ModelType.GEMINI_FLASH
        assert response.input_tokens == 20
        assert response.output_tokens == 15
        assert response.cost > 0
        assert response.quality_score > 0.7

def test_response_parsing_safety_block():
    """Test response parsing when blocked by safety filters"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        # Mock safety-blocked response
        api_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "I can't provide that content."}
                        ]
                    },
                    "finishReason": "SAFETY"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 5
            }
        }
        
        request = AIRequest(
            task_type="content_writing",
            complexity=2,
            content="Test request",
            user_tier="free"
        )
        
        from datetime import datetime
        start_time = datetime.utcnow()
        
        response = client._parse_response(api_response, request, ModelType.GEMINI_FLASH, start_time)
        
        assert response.content == "I can't provide that content."
        assert response.quality_score < 0.5  # Quality reduced due to safety block

def test_output_multipliers():
    """Test output token estimation multipliers for different tasks"""
    with patch('ai.clients.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        client = GeminiClient()
        
        test_content = "Test content with ten words to estimate tokens properly"
        
        # Test different task types
        tasks_and_expected_ratios = [
            ("code_generation", 2.5),
            ("component_generation", 3.0),
            ("content_writing", 2.0),
            ("summarization", 0.8),
            ("translation", 1.2)
        ]
        
        for task, expected_ratio in tasks_and_expected_ratios:
            estimate = client.estimate_cost(test_content, task, "gemini-1.5-flash")
            
            # Verify the ratio is approximately correct
            input_tokens = estimate["estimated_input_tokens"]
            output_tokens = estimate["estimated_output_tokens"]
            actual_ratio = output_tokens / input_tokens
            
            # Allow for some variance due to rounding
            assert abs(actual_ratio - expected_ratio) < 0.3, f"Task {task}: expected ~{expected_ratio}, got {actual_ratio}"