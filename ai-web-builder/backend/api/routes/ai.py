"""
AI service API routes for testing and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from auth.dependencies import get_current_user
from database.models import User
from ai.service import AIService
from ai.models import AIRequest, TaskType, UserTier, ModelType
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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

@router.post("/generate-component")
async def generate_component(
    description: str = Form(...),
    component_type: str = Form(...),
    complexity: int = Form(3),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a component with optional image reference"""
    try:
        # Validate inputs
        if component_type not in ["react", "html", "vue"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="component_type must be one of: react, html, vue"
            )
        
        if not 1 <= complexity <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="complexity must be between 1 and 5"
            )
        
        # Process image if uploaded
        image_data = None
        image_filename = None
        if image:
            # Validate image
            if not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            image_data = await image.read()
            if len(image_data) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image must be smaller than 10MB"
                )
            
            image_filename = image.filename
        
        # Generate component
        service = AIService(db)
        response = await service.process_multimodal_request(
            user=current_user,
            description=description,
            component_type=component_type,
            complexity=complexity,
            image_data=image_data,
            image_filename=image_filename
        )
        
        return {
            "success": True,
            "component_code": response.content,
            "component_type": component_type,
            "model_used": response.model_used.value,
            "cost": response.cost,
            "processing_time": response.processing_time,
            "quality_score": response.quality_score,
            "tokens": {
                "input": response.input_tokens,
                "output": response.output_tokens
            },
            "has_image_reference": image is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Component generation failed: {str(e)}"
        )

@router.post("/analyze-image")
async def analyze_component_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze an uploaded component image for replication insights"""
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        image_data = await image.read()
        if len(image_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image must be smaller than 10MB"
            )
        
        # Analyze image
        service = AIService(db)
        analysis = await service.analyze_component_image(image_data)
        
        if analysis.get("error"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image analysis failed: {analysis['error']}"
            )
        
        return {
            "success": True,
            "filename": image.filename,
            "analysis": analysis,
            "suggestions": {
                "component_type": analysis.get("component_type", "general component"),
                "recommended_complexity": analysis.get("suggested_complexity", 3),
                "layout_elements": analysis.get("layout_elements", []),
                "color_palette": analysis.get("color_palette", {}),
                "responsive_considerations": analysis.get("responsive_hint", "standard responsive design")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {str(e)}"
        )

@router.post("/estimate-multimodal-cost")
async def estimate_multimodal_cost(
    description: str = Form(...),
    component_type: str = Form(...),
    complexity: int = Form(3),
    has_image: bool = Form(False),
    current_user: User = Depends(get_current_user)
):
    """Estimate cost for multimodal component generation"""
    try:
        from ai.router import AIRouter
        
        # Create mock request for estimation
        request = AIRequest(
            task_type=TaskType.COMPONENT_GENERATION,
            complexity=complexity,
            content=description,
            user_tier=current_user.subscription_tier,
            requires_vision=has_image
        )
        
        router_instance = AIRouter()
        selection = router_instance.select_model(request)
        
        # Calculate cost breakdown
        estimated_tokens = {
            "input": len(description.split()) * 1.3,
            "output": len(description.split()) * 2.0  # Estimated output length
        }
        
        # Vision model cost adjustment
        vision_cost_adjustment = 0
        if has_image:
            vision_cost_adjustment = 0.01  # Base cost for image processing
        
        total_estimated_cost = selection.estimated_cost + vision_cost_adjustment
        
        return {
            "description_length": len(description),
            "component_type": component_type,
            "complexity": complexity,
            "has_image": has_image,
            "recommended_model": selection.model.value,
            "selection_confidence": selection.confidence,
            "selection_reason": selection.reason,
            "cost_breakdown": {
                "base_cost": selection.estimated_cost,
                "vision_cost": vision_cost_adjustment,
                "total_cost": total_estimated_cost
            },
            "estimated_tokens": estimated_tokens,
            "processing_time_estimate": f"{complexity * 0.8 + (2 if has_image else 0):.1f}s"
        }
        
    except Exception as e:
        logger.error(f"Multimodal cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )

@router.post("/validate-code")
async def validate_generated_code(
    code: str = Form(...),
    component_type: str = Form(...),
    complexity: int = Form(3),
    validation_level: str = Form("standard"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate AI-generated code for quality, security, and best practices"""
    try:
        from ai.quality_validator import AIQualityValidator, ValidationLevel
        
        # Validate inputs
        if component_type not in ["react", "html", "vue"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="component_type must be one of: react, html, vue"
            )
        
        if not 1 <= complexity <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="complexity must be between 1 and 5"
            )
        
        # Parse validation level
        try:
            level = ValidationLevel(validation_level)
        except ValueError:
            level = ValidationLevel.STANDARD
        
        # Initialize validator
        validator = AIQualityValidator(level)
        
        # Validate code
        validation_result = await validator.validate_code(code, component_type, complexity)
        
        return {
            "success": True,
            "validation_result": {
                "is_valid": validation_result.is_valid,
                "quality_score": {
                    "overall": validation_result.quality_score.overall,
                    "syntax": validation_result.quality_score.syntax,
                    "security": validation_result.quality_score.security,
                    "performance": validation_result.quality_score.performance,
                    "accessibility": validation_result.quality_score.accessibility,
                    "best_practices": validation_result.quality_score.best_practices,
                    "functionality": validation_result.quality_score.functionality
                },
                "issues": [
                    {
                        "category": issue.category.value,
                        "severity": issue.severity,
                        "message": issue.message,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion,
                        "code_snippet": issue.code_snippet
                    }
                    for issue in validation_result.issues
                ],
                "suggestions": validation_result.suggestions,
                "estimated_fix_time": validation_result.estimated_fix_time,
                "confidence": validation_result.confidence
            },
            "metadata": {
                "validation_level": validation_level,
                "component_type": component_type,
                "complexity": complexity,
                "code_length": len(code)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code validation failed: {str(e)}"
        )

@router.get("/validation-report/{user_id}")
async def get_user_validation_report(
    user_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's code quality validation report"""
    try:
        # Only allow users to see their own reports (or admins)
        if str(current_user.id) != user_id and current_user.subscription_tier != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get user's AI usage records with validation metadata
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(AIUsage).where(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_date,
                AIUsage.task_type == "component_generation"
            ).order_by(AIUsage.created_at.desc())
        )
        
        usage_records = result.scalars().all()
        
        if not usage_records:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_generations": 0,
                "average_quality": 0,
                "quality_trend": [],
                "common_issues": [],
                "improvement_suggestions": []
            }
        
        # Analyze validation data
        total_generations = len(usage_records)
        quality_scores = []
        all_issues = []
        
        for record in usage_records:
            metadata = record.metadata or {}
            validation = metadata.get('quality_validation', {})
            
            if validation.get('quality_score'):
                quality_scores.append(validation['quality_score'])
            
            # In a real implementation, you'd store detailed validation results
            # For now, we'll simulate some common issues
            if validation.get('issues_count', 0) > 0:
                all_issues.extend([
                    "Missing accessibility attributes",
                    "Performance optimization needed",
                    "Security best practices"
                ])
        
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Generate quality trend (last 10 generations)
        recent_scores = quality_scores[-10:] if len(quality_scores) >= 10 else quality_scores
        quality_trend = [{"generation": i+1, "score": score} for i, score in enumerate(recent_scores)]
        
        # Common issues analysis
        from collections import Counter
        issue_counts = Counter(all_issues)
        common_issues = [
            {"issue": issue, "frequency": count}
            for issue, count in issue_counts.most_common(5)
        ]
        
        # Generate improvement suggestions
        suggestions = []
        if average_quality < 70:
            suggestions.append("Focus on code structure and best practices")
        if average_quality < 80:
            suggestions.append("Improve accessibility and semantic HTML")
        if len(all_issues) > total_generations * 2:
            suggestions.append("Review generated code before implementation")
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_generations": total_generations,
            "average_quality": round(average_quality, 1),
            "quality_trend": quality_trend,
            "common_issues": common_issues,
            "improvement_suggestions": suggestions,
            "quality_distribution": {
                "excellent": len([s for s in quality_scores if s >= 90]),
                "good": len([s for s in quality_scores if 80 <= s < 90]),
                "average": len([s for s in quality_scores if 70 <= s < 80]),
                "poor": len([s for s in quality_scores if s < 70])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation report failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation report failed: {str(e)}"
        )

@router.get("/cache-stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache performance statistics for the current user"""
    try:
        service = AIService(db)
        stats = await service.get_cache_stats(str(current_user.id))
        
        return {
            "user_id": str(current_user.id),
            "cache_statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

@router.post("/optimize-cache")
async def optimize_user_cache(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize cache by removing old and unused entries"""
    try:
        service = AIService(db)
        
        # Only allow users to optimize their own cache (or admins to optimize global cache)
        if current_user.subscription_tier == "admin":
            result = await service.optimize_cache()
        else:
            # For regular users, just invalidate their cache
            result = await service.invalidate_user_cache(str(current_user.id))
        
        return {
            "success": True,
            "optimization_result": result
        }
        
    except Exception as e:
        logger.error(f"Cache optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache optimization failed: {str(e)}"
        )

@router.delete("/cache")
async def clear_user_cache(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all cache entries for the current user"""
    try:
        service = AIService(db)
        result = await service.invalidate_user_cache(str(current_user.id))
        
        return {
            "success": True,
            "message": f"Cache cleared for user {current_user.id}",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache clearing failed: {str(e)}"
        )

@router.get("/cache-efficiency-report")
async def get_cache_efficiency_report(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive cache efficiency report"""
    try:
        service = AIService(db)
        report = await service.get_cache_efficiency_report(current_user, days)
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Cache efficiency report failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache efficiency report failed: {str(e)}"
        )