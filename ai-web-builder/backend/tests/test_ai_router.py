"""
Tests for AI router and service
"""
import pytest
from ai.router import AIRouter
from ai.models import AIRequest, ModelType, TaskType, UserTier

def test_ai_router_initialization():
    """Test AI router initializes correctly"""
    router = AIRouter()
    assert router is not None
    assert len(router.performance_metrics) == len(ModelType)

def test_model_selection_simple_task():
    """Test model selection for simple tasks"""
    router = AIRouter()
    
    request = AIRequest(
        task_type=TaskType.CODE_GENERATION.value,
        complexity=2,
        content="Create a simple button component",
        user_tier=UserTier.FREE.value
    )
    
    selection = router.select_model(request)
    
    assert selection.model in [ModelType.DEEPSEEK_V3, ModelType.GEMINI_FLASH]
    assert selection.confidence > 0
    assert selection.estimated_cost < 0.01  # Should be very cheap for free tier

def test_model_selection_complex_task():
    """Test model selection for complex tasks"""
    router = AIRouter()
    
    request = AIRequest(
        task_type=TaskType.CAMPAIGN_ANALYSIS.value,
        complexity=8,
        content="Analyze this complex marketing campaign and provide detailed recommendations",
        user_tier=UserTier.AGENCY.value
    )
    
    selection = router.select_model(request)
    
    # Should select a premium model for complex tasks
    assert selection.model in [ModelType.CLAUDE_SONNET, ModelType.GPT4_TURBO]
    assert selection.confidence > 0.5

def test_model_selection_vision_required():
    """Test model selection when vision is required"""
    router = AIRouter()
    
    request = AIRequest(
        task_type=TaskType.DESIGN_REVIEW.value,
        complexity=5,
        content="Analyze this design screenshot",
        user_tier=UserTier.BUSINESS.value,
        requires_vision=True
    )
    
    selection = router.select_model(request)
    
    # Should select GPT-4V for vision tasks
    assert selection.model == ModelType.GPT4_VISION

def test_cost_estimation():
    """Test cost estimation for different models"""
    router = AIRouter()
    
    request = AIRequest(
        task_type=TaskType.CONTENT_WRITING.value,
        complexity=3,
        content="Write a 500-word blog post about AI",
        user_tier=UserTier.CREATOR.value
    )
    
    # Test cost estimation for different models
    deepseek_cost = router._estimate_cost(ModelType.DEEPSEEK_V3, request)
    claude_cost = router._estimate_cost(ModelType.CLAUDE_SONNET, request)
    
    # DeepSeek should be significantly cheaper
    assert deepseek_cost < claude_cost
    assert deepseek_cost < 0.01  # Should be very cheap

def test_get_model_recommendations():
    """Test getting model recommendations"""
    router = AIRouter()
    
    recommendations = router.get_model_recommendations(
        TaskType.CODE_GENERATION.value,
        UserTier.CREATOR.value
    )
    
    assert len(recommendations) <= 3
    assert ModelType.DEEPSEEK_V3 in recommendations  # Should recommend cost-effective option

def test_cost_analysis():
    """Test cost analysis across models"""
    router = AIRouter()
    
    cost_analysis = router.get_cost_analysis(
        content_length=100,
        task_type=TaskType.COMPONENT_GENERATION.value
    )
    
    assert len(cost_analysis) == len(ModelType)
    assert cost_analysis[ModelType.DEEPSEEK_V3] < cost_analysis[ModelType.GPT4_TURBO]