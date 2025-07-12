"""
AI Service - Main interface for AI operations with cost tracking
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict

from .router import AIRouter, ModelSelection
from .models import AIRequest, AIResponse, ModelType, TaskType
from database.models import User, AIUsage
from database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings

logger = logging.getLogger(__name__)

class AIService:
    """
    Main AI service with intelligent routing and cost tracking
    """
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.router = AIRouter()
        self.client_cache = {}  # Cache for AI clients
    
    async def process_request(
        self, 
        user: User, 
        request: AIRequest,
        validate_budget: bool = True
    ) -> AIResponse:
        """
        Process an AI request with intelligent model selection and cost tracking
        
        Args:
            user: User making the request
            request: AI request details
            validate_budget: Whether to check user's budget before processing
            
        Returns:
            AIResponse with generated content and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate user's budget if requested
            if validate_budget:
                await self._validate_user_budget(user, request)
            
            # Select optimal model
            selection = self.router.select_model(request)
            logger.info(f"Selected model {selection.model.value} for user {user.id}: {selection.reason}")
            
            # Check if estimated cost exceeds user's remaining budget
            if validate_budget:
                remaining_budget = await self._get_remaining_budget(user)
                if selection.estimated_cost > remaining_budget:
                    # Try with a cheaper model
                    cheaper_selection = await self._select_cheaper_model(request, remaining_budget)
                    if cheaper_selection:
                        selection = cheaper_selection
                    else:
                        raise ValueError(f"Insufficient budget. Need ${selection.estimated_cost:.4f}, have ${remaining_budget:.4f}")
            
            # Process with selected model
            response = await self._process_with_model(selection.model, request)
            
            # Track usage and costs
            await self._track_usage(user, request, response, selection)
            
            # Update router performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            response.processing_time = processing_time
            self.router.update_performance_metrics(response)
            
            logger.info(f"AI request completed for user {user.id}: {response.model_used.value} cost=${response.cost:.4f}")
            return response
            
        except Exception as e:
            logger.error(f"AI request failed for user {user.id}: {str(e)}")
            
            # Try fallback model if available
            if hasattr(request, 'allow_fallback') and request.allow_fallback:
                try:
                    fallback_response = await self._try_fallback(user, request)
                    if fallback_response:
                        return fallback_response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            raise
    
    async def _validate_user_budget(self, user: User, request: AIRequest):
        """Validate user has sufficient budget for the request"""
        # Get user's subscription limits
        subscription_limits = settings.SUBSCRIPTION_LIMITS.get(user.subscription_tier, {})
        monthly_ai_limit = subscription_limits.get("ai_credits", 0) * 0.01  # Convert credits to dollars
        
        # Get current month usage
        current_usage = await self._get_monthly_usage(user)
        
        if current_usage >= monthly_ai_limit:
            raise ValueError(f"Monthly AI budget exceeded. Used ${current_usage:.2f} of ${monthly_ai_limit:.2f}")
    
    async def _get_remaining_budget(self, user: User) -> float:
        """Get user's remaining AI budget for the month"""
        subscription_limits = settings.SUBSCRIPTION_LIMITS.get(user.subscription_tier, {})
        monthly_ai_limit = subscription_limits.get("ai_credits", 0) * 0.01
        
        current_usage = await self._get_monthly_usage(user)
        return max(0, monthly_ai_limit - current_usage)
    
    async def _get_monthly_usage(self, user: User) -> float:
        """Get user's AI usage for current month"""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(AIUsage).where(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= month_start
            )
        )
        
        usage_records = result.scalars().all()
        return sum(record.cost for record in usage_records)
    
    async def _select_cheaper_model(self, request: AIRequest, max_cost: float) -> Optional[ModelSelection]:
        """Select a cheaper model that fits within budget"""
        # Create a new request with max cost constraint
        constrained_request = AIRequest(
            task_type=request.task_type,
            complexity=max(1, request.complexity - 1),  # Reduce complexity slightly
            content=request.content,
            user_tier=request.user_tier,
            max_cost=max_cost,
            requires_vision=request.requires_vision
        )
        
        selection = self.router.select_model(constrained_request)
        
        if selection.estimated_cost <= max_cost:
            return selection
        return None
    
    async def _process_with_model(self, model: ModelType, request: AIRequest) -> AIResponse:
        """Process request with specific AI model"""
        logger.info(f"Processing with {model.value}: {request.task_type}")
        
        try:
            if model == ModelType.DEEPSEEK_V3:
                return await self._process_with_deepseek(request)
            elif model == ModelType.GEMINI_FLASH:
                return await self._process_with_gemini(request, "gemini-1.5-flash")
            elif model == ModelType.GEMINI_PRO:
                return await self._process_with_gemini(request, "gemini-1.5-pro") 
            elif model == ModelType.CLAUDE_SONNET:
                return await self._process_with_claude(request)
            elif model == ModelType.GPT4_TURBO:
                return await self._process_with_openai(request, "gpt-4-turbo")
            elif model == ModelType.GPT4_VISION:
                return await self._process_with_openai(request, "gpt-4-vision-preview")
            else:
                # Fallback to mock response
                return await self._process_mock_response(model, request)
                
        except Exception as e:
            logger.error(f"Error processing with {model.value}: {e}")
            # Return mock response as fallback during development
            return await self._process_mock_response(model, request)
    
    async def _process_with_deepseek(self, request: AIRequest) -> AIResponse:
        """Process request with DeepSeek V3"""
        from .clients.deepseek import DeepSeekClient
        
        async with DeepSeekClient() as client:
            # Adjust temperature based on task type
            temperature = 0.3 if request.task_type in ["code_generation", "component_generation"] else 0.7
            
            response = await client.generate_completion(
                request,
                temperature=temperature,
                max_tokens=4000
            )
            
            return response
    
    async def _process_with_gemini(self, request: AIRequest, model_name: str) -> AIResponse:
        """Process request with Google Gemini"""
        from .clients.gemini import GeminiClient
        
        async with GeminiClient() as client:
            # Adjust temperature based on task type and complexity
            temperature = 0.3 if request.task_type in ["code_generation", "component_generation"] else 0.7
            if request.complexity <= 3:
                temperature *= 0.8  # Lower temperature for simple tasks
            
            # Set appropriate max tokens based on task
            max_tokens = None
            if request.task_type == "summarization":
                max_tokens = 1000  # Shorter outputs for summaries
            elif request.task_type in ["code_generation", "component_generation"]:
                max_tokens = 4000  # Longer outputs for code
            
            response = await client.generate_completion(
                request,
                model_variant=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
    
    async def _process_with_claude(self, request: AIRequest) -> AIResponse:
        """Process request with Claude Sonnet"""
        # Placeholder for Claude implementation
        logger.info(f"Claude processing not yet implemented, using mock response")
        return await self._process_mock_response(ModelType.CLAUDE_SONNET, request)
    
    async def _process_with_openai(self, request: AIRequest, model_name: str) -> AIResponse:
        """Process request with OpenAI models"""
        # Placeholder for OpenAI implementation
        logger.info(f"OpenAI processing not yet implemented, using mock response")
        return await self._process_mock_response(
            ModelType.GPT4_VISION if "vision" in model_name else ModelType.GPT4_TURBO,
            request
        )
    
    async def _process_mock_response(self, model: ModelType, request: AIRequest) -> AIResponse:
        """Generate mock response for development/fallback"""
        # Simulate processing time based on model
        processing_times = {
            ModelType.DEEPSEEK_V3: 2.0,
            ModelType.GEMINI_FLASH: 1.5,
            ModelType.GEMINI_PRO: 3.0,
            ModelType.CLAUDE_SONNET: 4.0,
            ModelType.GPT4_TURBO: 5.0,
            ModelType.GPT4_VISION: 6.0
        }
        
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Mock response generation
        input_tokens = len(request.content.split()) * 1.3
        output_tokens = input_tokens * 1.5  # Mock output length
        
        # Calculate actual cost
        from .models import MODEL_COSTS
        model_costs = MODEL_COSTS[model]
        cost = model_costs.calculate_cost(
            int(input_tokens),
            int(output_tokens),
            1 if request.requires_vision else 0
        )
        
        # Mock generated content based on task type
        mock_content = self._generate_mock_content(request.task_type, request.content)
        
        return AIResponse(
            content=mock_content,
            model_used=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=cost,
            quality_score=0.85,  # Mock quality score
            processing_time=processing_times.get(model, 3.0)
        )
    
    def _generate_mock_content(self, task_type: str, input_content: str) -> str:
        """Generate mock content for testing purposes"""
        mock_responses = {
            TaskType.CODE_GENERATION.value: f"// Generated React component based on: {input_content[:50]}...\nexport const Component = () => {{ return <div>Generated content</div>; }};",
            TaskType.CONTENT_WRITING.value: f"Here's compelling content based on your request: {input_content[:50]}...\n\nThis is professionally written content that addresses your needs.",
            TaskType.ANALYSIS.value: f"Analysis of: {input_content[:50]}...\n\nKey findings:\n1. Primary insight\n2. Secondary observation\n3. Recommendation",
            TaskType.COMPONENT_GENERATION.value: f"import React from 'react';\n\n// Component generated from: {input_content[:30]}...\nexport const GeneratedComponent = () => {{\n  return (\n    <div className=\"generated-component\">\n      <h1>Generated Component</h1>\n    </div>\n  );\n}};",
            TaskType.CAMPAIGN_ANALYSIS.value: f"Campaign Analysis Report\n\nBased on: {input_content[:50]}...\n\nPerformance Score: 75/100\nRecommendations:\n- Improve headline\n- Optimize call-to-action\n- Enhance visual design"
        }
        
        return mock_responses.get(task_type, f"Generated response for {task_type}: {input_content[:100]}...")
    
    async def _track_usage(self, user: User, request: AIRequest, response: AIResponse, selection: ModelSelection):
        """Track AI usage in database"""
        usage_record = AIUsage(
            user_id=user.id,
            model_used=response.model_used.value,
            task_type=request.task_type,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=response.cost,
            processing_time=response.processing_time,
            quality_score=response.quality_score,
            user_tier=user.subscription_tier,
            metadata={
                "complexity": request.complexity,
                "selection_confidence": selection.confidence,
                "estimated_cost": selection.estimated_cost,
                "content_length": len(request.content)
            }
        )
        
        self.db.add(usage_record)
        await self.db.commit()
        
        # Cache usage stats in Redis if available
        if self.redis:
            await self._cache_usage_stats(user, response.cost)
    
    async def _cache_usage_stats(self, user: User, cost: float):
        """Cache usage statistics in Redis"""
        try:
            # Update daily usage
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_key = f"ai_usage:daily:{user.id}:{today}"
            await self.redis.incrbyfloat(daily_key, cost)
            await self.redis.expire(daily_key, 86400 * 7)  # Keep for 7 days
            
            # Update monthly usage
            month = datetime.utcnow().strftime("%Y-%m")
            monthly_key = f"ai_usage:monthly:{user.id}:{month}"
            await self.redis.incrbyfloat(monthly_key, cost)
            await self.redis.expire(monthly_key, 86400 * 32)  # Keep for 32 days
            
        except Exception as e:
            logger.warning(f"Failed to cache usage stats: {e}")
    
    async def _try_fallback(self, user: User, request: AIRequest) -> Optional[AIResponse]:
        """Try fallback model if primary fails"""
        # Use DeepSeek as ultimate fallback for cost efficiency
        fallback_request = AIRequest(
            task_type=request.task_type,
            complexity=min(3, request.complexity),  # Reduce complexity for fallback
            content=request.content,
            user_tier=request.user_tier,
            requires_vision=False  # Disable vision for fallback
        )
        
        try:
            response = await self._process_with_model(ModelType.DEEPSEEK_V3, fallback_request)
            await self._track_usage(user, fallback_request, response, 
                                  ModelSelection(
                                      model=ModelType.DEEPSEEK_V3,
                                      confidence=0.5,
                                      reason="Fallback selection",
                                      estimated_cost=response.cost,
                                      fallbacks=[]
                                  ))
            return response
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return None
    
    async def get_usage_analytics(self, user: User, days: int = 30) -> Dict[str, Any]:
        """Get user's AI usage analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(AIUsage).where(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= start_date
            ).order_by(AIUsage.created_at.desc())
        )
        
        usage_records = result.scalars().all()
        
        if not usage_records:
            return {
                "total_cost": 0,
                "total_requests": 0,
                "avg_cost_per_request": 0,
                "model_usage": {},
                "task_type_usage": {},
                "daily_usage": {}
            }
        
        # Calculate analytics
        total_cost = sum(record.cost for record in usage_records)
        total_requests = len(usage_records)
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        
        # Model usage breakdown
        model_usage = {}
        for record in usage_records:
            model = record.model_used
            if model not in model_usage:
                model_usage[model] = {"count": 0, "cost": 0}
            model_usage[model]["count"] += 1
            model_usage[model]["cost"] += record.cost
        
        # Task type breakdown
        task_type_usage = {}
        for record in usage_records:
            task = record.task_type
            if task not in task_type_usage:
                task_type_usage[task] = {"count": 0, "cost": 0}
            task_type_usage[task]["count"] += 1
            task_type_usage[task]["cost"] += record.cost
        
        # Daily usage
        daily_usage = {}
        for record in usage_records:
            day = record.created_at.strftime("%Y-%m-%d")
            if day not in daily_usage:
                daily_usage[day] = {"cost": 0, "requests": 0}
            daily_usage[day]["cost"] += record.cost
            daily_usage[day]["requests"] += 1
        
        return {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "avg_cost_per_request": avg_cost,
            "model_usage": model_usage,
            "task_type_usage": task_type_usage,
            "daily_usage": daily_usage,
            "period_days": days
        }
    
    async def get_cost_optimization_suggestions(self, user: User) -> List[Dict[str, Any]]:
        """Get personalized cost optimization suggestions"""
        analytics = await self.get_usage_analytics(user, 30)
        suggestions = []
        
        # Analyze model usage patterns
        model_usage = analytics.get("model_usage", {})
        total_cost = analytics.get("total_cost", 0)
        
        if total_cost == 0:
            return suggestions
        
        # Suggest switching expensive models to cheaper alternatives
        expensive_models = ["gpt-4-turbo", "claude-3.5-sonnet"]
        for model in expensive_models:
            if model in model_usage:
                usage = model_usage[model]
                if usage["cost"] / total_cost > 0.3:  # If this model accounts for >30% of costs
                    suggestions.append({
                        "type": "model_optimization",
                        "priority": "high",
                        "title": f"Consider alternatives to {model}",
                        "description": f"You're spending ${usage['cost']:.2f} on {model}. Try Gemini Pro or DeepSeek for similar tasks.",
                        "potential_savings": usage["cost"] * 0.7  # Estimate 70% savings
                    })
        
        # Suggest task optimization
        task_usage = analytics.get("task_type_usage", {})
        for task, usage in task_usage.items():
            if usage["cost"] / total_cost > 0.4:  # If task accounts for >40% of costs
                suggestions.append({
                    "type": "task_optimization", 
                    "priority": "medium",
                    "title": f"Optimize {task} requests",
                    "description": f"Consider batching {task} requests or using templates to reduce AI calls.",
                    "potential_savings": usage["cost"] * 0.3  # Estimate 30% savings
                })
        
        return suggestions