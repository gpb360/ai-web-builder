"""
AI service API routes for testing and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from auth.dependencies import get_current_user
from database.models import User
from ai.service import AIService
from ai.models import AIRequest, TaskType, UserTier, ModelType
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/test-generation")
async def test_ai_generation(
    task_type: str,
    content: str,
    complexity: int = 3,
    model_preference: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test AI generation with different models"""
    try:
        service = AIService(db)
        
        request = AIRequest(
            task_type=task_type,
            complexity=complexity,
            content=content,
            user_tier=current_user.subscription_tier,
            requires_vision=False
        )
        
        # If specific model requested, override router selection
        if model_preference:
            try:
                model_type = ModelType(model_preference)
                response = await service._process_with_model(model_type, request)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid model type: {model_preference}"
                )
        else:
            # Use router for optimal selection
            response = await service.process_request(current_user, request, validate_budget=False)
        
        return {
            "success": True,
            "content": response.content,
            "model_used": response.model_used.value,
            "cost": response.cost,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "quality_score": response.quality_score,
            "processing_time": response.processing_time
        }
        
    except Exception as e:
        logger.error(f"AI generation test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )

@router.get("/test-connections")
async def test_ai_connections(
    current_user: User = Depends(get_current_user)
):
    """Test connections to all AI providers"""
    results = {}
    
    # Test DeepSeek
    try:
        from ai.clients.deepseek import DeepSeekClient
        async with DeepSeekClient() as client:
            results["deepseek"] = await client.test_connection()
    except Exception as e:
        results["deepseek"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Test Gemini
    try:
        from ai.clients.gemini import GeminiClient
        async with GeminiClient() as client:
            results["gemini"] = await client.test_connection()
    except Exception as e:
        results["gemini"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Placeholder for other providers
    results["claude"] = {"success": False, "error": "Not implemented"}
    results["openai"] = {"success": False, "error": "Not implemented"}
    
    return {
        "timestamp": "2024-12-10T00:00:00Z",
        "connections": results,
        "summary": {
            "total_providers": len(results),
            "successful": sum(1 for r in results.values() if r.get("success", False)),
            "failed": sum(1 for r in results.values() if not r.get("success", False))
        }
    }

@router.get("/cost-analysis")
async def get_cost_analysis(
    content_length: int = 100,
    task_type: str = "component_generation",
    current_user: User = Depends(get_current_user)
):
    """Get cost analysis across all AI models"""
    try:
        from ai.router import AIRouter
        
        router_instance = AIRouter()
        cost_analysis = router_instance.get_cost_analysis(content_length, task_type)
        
        # Sort by cost
        sorted_costs = sorted(
            [(model.value, cost) for model, cost in cost_analysis.items()],
            key=lambda x: x[1]
        )
        
        return {
            "task_type": task_type,
            "content_length": content_length,
            "costs": {model: cost for model, cost in sorted_costs},
            "cheapest": sorted_costs[0],
            "most_expensive": sorted_costs[-1],
            "cost_range": {
                "min": sorted_costs[0][1],
                "max": sorted_costs[-1][1],
                "savings_percent": ((sorted_costs[-1][1] - sorted_costs[0][1]) / sorted_costs[-1][1]) * 100
            }
        }
        
    except Exception as e:
        logger.error(f"Cost analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost analysis failed: {str(e)}"
        )

@router.get("/model-recommendations")
async def get_model_recommendations(
    task_type: str,
    current_user: User = Depends(get_current_user)
):
    """Get model recommendations for a specific task type and user tier"""
    try:
        from ai.router import AIRouter
        
        router_instance = AIRouter()
        recommendations = router_instance.get_model_recommendations(
            task_type, 
            current_user.subscription_tier
        )
        
        # Get cost estimates for recommendations
        cost_estimates = []
        for model in recommendations:
            mock_request = AIRequest(
                task_type=task_type,
                complexity=5,
                content="Sample content for estimation",
                user_tier=current_user.subscription_tier
            )
            cost = router_instance._estimate_cost(model, mock_request)
            cost_estimates.append({
                "model": model.value,
                "estimated_cost": cost,
                "capabilities": router_instance.performance_metrics[model]
            })
        
        return {
            "task_type": task_type,
            "user_tier": current_user.subscription_tier,
            "recommendations": cost_estimates,
            "selection_criteria": {
                "cost_efficiency": "40%",
                "task_suitability": "30%", 
                "historical_performance": "20%",
                "user_tier_appropriateness": "10%"
            }
        }
        
    except Exception as e:
        logger.error(f"Model recommendations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model recommendations failed: {str(e)}"
        )

@router.get("/usage-analytics")
async def get_user_usage_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's AI usage analytics"""
    try:
        service = AIService(db)
        analytics = await service.get_usage_analytics(current_user, days)
        
        return {
            "user_id": str(current_user.id),
            "period_days": days,
            "analytics": analytics,
            "cost_optimization": await service.get_cost_optimization_suggestions(current_user)
        }
        
    except Exception as e:
        logger.error(f"Usage analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage analytics failed: {str(e)}"
        )

@router.post("/estimate-cost")
async def estimate_request_cost(
    task_type: str,
    content: str,
    complexity: int = 3,
    model_preference: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Estimate cost for an AI request without executing it"""
    try:
        from ai.router import AIRouter
        
        request = AIRequest(
            task_type=task_type,
            complexity=complexity,
            content=content,
            user_tier=current_user.subscription_tier
        )
        
        router_instance = AIRouter()
        
        if model_preference:
            try:
                model_type = ModelType(model_preference)
                cost = router_instance._estimate_cost(model_type, request)
                return {
                    "requested_model": model_preference,
                    "estimated_cost": cost,
                    "task_type": task_type,
                    "complexity": complexity
                }
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid model type: {model_preference}"
                )
        else:
            # Get optimal selection and alternatives
            selection = router_instance.select_model(request)
            
            # Get costs for top 3 options
            alternatives = []
            for model in [selection.model] + selection.fallbacks[:2]:
                cost = router_instance._estimate_cost(model, request)
                alternatives.append({
                    "model": model.value,
                    "estimated_cost": cost,
                    "is_recommended": model == selection.model
                })
            
            return {
                "recommended_selection": {
                    "model": selection.model.value,
                    "confidence": selection.confidence,
                    "reason": selection.reason,
                    "estimated_cost": selection.estimated_cost
                },
                "alternatives": alternatives,
                "task_type": task_type,
                "complexity": complexity
            }
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )

@router.get("/available-models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    """Get list of available AI models with their capabilities"""
    try:
        from ai.models import MODEL_CAPABILITIES, MODEL_COSTS
        
        models_info = []
        for model_type in ModelType:
            capabilities = MODEL_CAPABILITIES.get(model_type, {})
            costs = MODEL_COSTS.get(model_type)
            
            model_info = {
                "model": model_type.value,
                "capabilities": capabilities,
                "pricing": {
                    "input_cost_per_1m_tokens": costs.input_cost if costs else 0,
                    "output_cost_per_1m_tokens": costs.output_cost if costs else 0,
                    "image_cost": costs.image_cost if costs and costs.image_cost else None
                },
                "recommended_for": capabilities.get("strengths", []),
                "max_complexity": capabilities.get("max_complexity", 5),
                "quality_tier": capabilities.get("quality_tier", "unknown")
            }
            
            models_info.append(model_info)
        
        return {
            "available_models": models_info,
            "user_tier": current_user.subscription_tier,
            "total_models": len(models_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available models: {str(e)}"
        )