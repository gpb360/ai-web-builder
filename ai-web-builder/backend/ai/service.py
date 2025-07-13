"""
AI Service - Main interface for AI operations with cost tracking
"""
import logging
import asyncio
import base64
import io
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict
from PIL import Image

from .router import AIRouter, ModelSelection
from .models import AIRequest, AIResponse, ModelType, TaskType
from .cost_tracker import CostTracker, CostAlert, BudgetStatus
from .quality_validator import AIQualityValidator, ValidationLevel, ValidationResult
from .cache_manager import AICacheManager
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
        self.cost_tracker = CostTracker(db, redis_client)
        self.quality_validator = AIQualityValidator(ValidationLevel.STANDARD)
        self.cache_manager = AICacheManager(redis_client, db) if redis_client else None
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
            # Check cache first if caching is enabled
            if self.cache_manager:
                cached_response = await self.cache_manager.get_cached_response(request, str(user.id))
                if cached_response:
                    logger.info(f"Returning cached response for user {user.id}: ${cached_response.cost:.4f} saved")
                    return cached_response
            
            # Select optimal model
            selection = self.router.select_model(request)
            logger.info(f"Selected model {selection.model.value} for user {user.id}: {selection.reason}")
            
            # Check budget before proceeding if validation enabled
            if validate_budget:
                budget_check = await self.cost_tracker.check_request_budget(user, selection.estimated_cost)
                if not budget_check['can_proceed']:
                    # Try with a cheaper model
                    cheaper_selection = await self._select_cheaper_model(request, budget_check['remaining_budget'])
                    if cheaper_selection:
                        selection = cheaper_selection
                    else:
                        raise ValueError(
                            f"Insufficient budget. Need ${selection.estimated_cost:.4f}, "
                            f"have ${budget_check['remaining_budget']:.4f} remaining"
                        )
            
            # Process with selected model
            response = await self._process_with_model(selection.model, request)
            
            # Track usage and costs with real-time monitoring
            alert = await self.cost_tracker.track_request_cost(
                user, 
                request, 
                response, 
                {
                    'selection_confidence': selection.confidence,
                    'selection_reason': selection.reason,
                    'fallbacks': [m.value for m in selection.fallbacks]
                }
            )
            
            # Handle cost alerts
            if alert:
                logger.warning(f"Cost alert for user {user.id}: {alert.message}")
                # In production, you might send notifications here
            
            # Update router performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            response.processing_time = processing_time
            self.router.update_performance_metrics(response)
            
            # Cache the response if caching is enabled and response is valid
            if self.cache_manager and response.quality_score and response.quality_score > 0.7:
                await self.cache_manager.cache_response(request, response, str(user.id))
            
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
    
    async def process_multimodal_request(
        self,
        user: User,
        description: str,
        component_type: str,
        complexity: int,
        image_data: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        validate_budget: bool = True
    ) -> AIResponse:
        """
        Process a multimodal AI request (text + optional image)
        
        Args:
            user: User making the request
            description: Text description of the component to generate
            component_type: Type of component ('react', 'html', 'vue')
            complexity: Complexity level (1-5)
            image_data: Binary image data
            image_filename: Original filename for metadata
            validate_budget: Whether to check user's budget
            
        Returns:
            AIResponse with generated component code
        """
        # Process image if provided
        image_analysis = None
        if image_data:
            image_analysis = await self._analyze_image(image_data, image_filename)
        
        # Create enhanced prompt with image analysis
        enhanced_content = self._create_multimodal_prompt(
            description, component_type, complexity, image_analysis
        )
        
        # Determine if vision model is needed
        requires_vision = image_data is not None
        
        # Create AI request
        request = AIRequest(
            task_type=TaskType.COMPONENT_GENERATION,
            complexity=complexity,
            content=enhanced_content,
            user_tier=user.subscription_tier,
            requires_vision=requires_vision
        )
        
        # Process the request
        response = await self.process_request(user, request, validate_budget)
        
        # Validate the generated code quality if it's a component generation task
        if request.task_type == TaskType.COMPONENT_GENERATION and response.content:
            try:
                validation_result = await self.quality_validator.validate_code(
                    response.content, 
                    component_type, 
                    complexity
                )
                
                # Store validation results in response metadata
                if hasattr(response, 'metadata'):
                    response.metadata.update({
                        'quality_validation': {
                            'is_valid': validation_result.is_valid,
                            'quality_score': validation_result.quality_score.overall,
                            'issues_count': len(validation_result.issues),
                            'confidence': validation_result.confidence,
                            'estimated_fix_time': validation_result.estimated_fix_time
                        }
                    })
                else:
                    response.metadata = {
                        'quality_validation': {
                            'is_valid': validation_result.is_valid,
                            'quality_score': validation_result.quality_score.overall,
                            'issues_count': len(validation_result.issues),
                            'confidence': validation_result.confidence,
                            'estimated_fix_time': validation_result.estimated_fix_time
                        }
                    }
                
                # Update quality score in response
                if validation_result.confidence > 0.7:  # Only update if we're confident
                    response.quality_score = validation_result.quality_score.overall / 100
                
                logger.info(f"Quality validation completed: {validation_result.quality_score.overall:.1f}% quality")
                
            except Exception as e:
                logger.warning(f"Quality validation failed: {e}")
                # Don't fail the entire request if validation fails
        
        return response
    
    async def _analyze_image(self, image_data: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze uploaded image for component generation context
        
        Args:
            image_data: Binary image data
            filename: Original filename
            
        Returns:
            Dictionary with image analysis results
        """
        try:
            # Convert to PIL Image for basic analysis
            image = Image.open(io.BytesIO(image_data))
            
            # Basic image properties
            analysis = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "filename": filename,
                "size_kb": len(image_data) / 1024,
                "aspect_ratio": round(image.width / image.height, 2),
                "is_landscape": image.width > image.height,
                "is_square": abs(image.width - image.height) < min(image.width, image.height) * 0.1
            }
            
            # Convert to base64 for AI processing
            analysis["base64"] = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image characteristics for prompt enhancement
            if analysis["aspect_ratio"] > 2:
                analysis["layout_hint"] = "wide banner or header component"
            elif analysis["aspect_ratio"] < 0.5:
                analysis["layout_hint"] = "tall sidebar or mobile component"
            elif analysis["is_square"]:
                analysis["layout_hint"] = "square card or avatar component"
            else:
                analysis["layout_hint"] = "standard rectangular component"
            
            # Size recommendations
            if analysis["width"] > 1200:
                analysis["responsive_hint"] = "large desktop component, ensure mobile responsiveness"
            elif analysis["width"] < 400:
                analysis["responsive_hint"] = "mobile-first component"
            else:
                analysis["responsive_hint"] = "standard responsive component"
            
            logger.info(f"Image analyzed: {analysis['width']}x{analysis['height']}, {analysis['size_kb']:.1f}KB")
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "filename": filename,
                "size_kb": len(image_data) / 1024 if image_data else 0,
                "layout_hint": "standard component",
                "responsive_hint": "responsive component"
            }
    
    def _create_multimodal_prompt(
        self,
        description: str,
        component_type: str,
        complexity: int,
        image_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create enhanced prompt for multimodal component generation
        
        Args:
            description: User's text description
            component_type: Type of component to generate
            complexity: Complexity level
            image_analysis: Results from image analysis
            
        Returns:
            Enhanced prompt string
        """
        prompt_parts = []
        
        # Base prompt
        prompt_parts.append(f"""Create a {component_type.upper()} component based on the following requirements:

Description: {description}
Component Type: {component_type}
Complexity Level: {complexity}/5""")
        
        # Add image context if available
        if image_analysis and not image_analysis.get("error"):
            prompt_parts.append(f"""

VISUAL REFERENCE PROVIDED:
- Image dimensions: {image_analysis.get('width', 'unknown')}x{image_analysis.get('height', 'unknown')}
- Layout suggestion: {image_analysis.get('layout_hint', 'standard component')}
- Responsive consideration: {image_analysis.get('responsive_hint', 'responsive component')}
- Aspect ratio: {image_analysis.get('aspect_ratio', '1.0')}

Please analyze the provided image and incorporate its visual elements, layout, color scheme, and design patterns into the generated component. Match the styling and structure as closely as possible while adapting it to {component_type} best practices.""")
        
        # Add complexity-specific requirements
        complexity_requirements = {
            1: "Keep it simple with basic HTML structure and minimal CSS",
            2: "Add basic interactivity and hover effects",
            3: "Include responsive design and form validation if applicable",
            4: "Add advanced animations, state management, and error handling",
            5: "Implement enterprise-level features, performance optimizations, and accessibility"
        }
        
        prompt_parts.append(f"""

COMPLEXITY REQUIREMENTS ({complexity}/5):
{complexity_requirements.get(complexity, 'Standard complexity')}""")
        
        # Add framework-specific requirements
        framework_requirements = {
            "react": """
REACT REQUIREMENTS:
- Use TypeScript with proper type definitions
- Include React hooks (useState, useEffect) as needed
- Follow React best practices and naming conventions
- Use functional components
- Include proper prop interfaces
- Add JSX comments for complex logic""",
            "html": """
HTML REQUIREMENTS:
- Use semantic HTML5 elements
- Include proper DOCTYPE and meta tags
- Embed CSS in <style> section
- Add JavaScript in <script> section if needed
- Ensure cross-browser compatibility
- Use proper accessibility attributes""",
            "vue": """
VUE REQUIREMENTS:
- Use Vue 3 Composition API with <script setup>
- Include TypeScript typing where appropriate
- Use reactive references (ref, computed) as needed
- Follow Vue naming conventions
- Include proper template structure
- Add scoped styles"""
        }
        
        prompt_parts.append(framework_requirements.get(component_type, ""))
        
        # Add general requirements
        prompt_parts.append("""

GENERAL REQUIREMENTS:
- Ensure the component is production-ready
- Include responsive design for mobile, tablet, and desktop
- Use modern CSS techniques (flexbox, grid, custom properties)
- Add accessibility features (ARIA labels, keyboard navigation)
- Include hover and focus states for interactive elements
- Use consistent spacing and typography
- Ensure proper contrast ratios for readability
- Add loading states and error handling where appropriate

OUTPUT FORMATTING:
- Provide clean, well-formatted code
- Include necessary imports and dependencies
- Add brief comments for complex logic
- Ensure code is copy-paste ready""")
        
        return "\n".join(prompt_parts)
    
    async def analyze_component_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze an image of an existing component for replication
        
        Args:
            image_data: Binary image data of component screenshot
            
        Returns:
            Analysis results with component characteristics
        """
        try:
            image_analysis = await self._analyze_image(image_data)
            
            # Enhanced analysis for component replication
            analysis = {
                **image_analysis,
                "component_type": self._detect_component_type(image_analysis),
                "suggested_complexity": self._suggest_complexity_from_image(image_analysis),
                "color_palette": self._extract_color_hints(image_analysis),
                "layout_elements": self._identify_layout_elements(image_analysis)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Component image analysis failed: {e}")
            return {"error": str(e)}
    
    def _detect_component_type(self, image_analysis: Dict[str, Any]) -> str:
        """Detect likely component type from image characteristics"""
        aspect_ratio = image_analysis.get("aspect_ratio", 1.0)
        
        if aspect_ratio > 3:
            return "header or navigation component"
        elif aspect_ratio < 0.3:
            return "sidebar or vertical menu component"
        elif 0.8 <= aspect_ratio <= 1.2:
            return "card or modal component"
        else:
            return "general layout component"
    
    def _suggest_complexity_from_image(self, image_analysis: Dict[str, Any]) -> int:
        """Suggest complexity level based on image characteristics"""
        # This is a simplified heuristic - in production, you'd use actual image analysis
        width = image_analysis.get("width", 400)
        height = image_analysis.get("height", 300)
        
        # Larger images might indicate more complex components
        pixel_count = width * height
        
        if pixel_count < 50000:  # Small images (< 223x223)
            return 2
        elif pixel_count < 200000:  # Medium images (< 447x447)
            return 3
        elif pixel_count < 500000:  # Large images (< 707x707)
            return 4
        else:
            return 5
    
    def _extract_color_hints(self, image_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Extract color palette hints from image (simplified)"""
        # In production, you'd analyze actual pixel data
        return {
            "primary": "#3B82F6",  # Default blue
            "secondary": "#6B7280",  # Default gray
            "accent": "#10B981",   # Default green
            "background": "#FFFFFF",
            "text": "#1F2937"
        }
    
    def _identify_layout_elements(self, image_analysis: Dict[str, Any]) -> List[str]:
        """Identify likely layout elements from image (simplified)"""
        elements = ["container", "content"]
        
        aspect_ratio = image_analysis.get("aspect_ratio", 1.0)
        
        if aspect_ratio > 2:
            elements.extend(["header", "navigation"])
        elif aspect_ratio < 0.5:
            elements.extend(["sidebar", "menu"])
        else:
            elements.extend(["card", "button", "text"])
        
        return elements
    
    async def get_cache_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not self.cache_manager:
            return {"error": "Caching not enabled"}
        
        try:
            stats = await self.cache_manager.get_cache_stats(user_id)
            return {
                "cache_enabled": True,
                "stats": {
                    "total_requests": stats.total_requests,
                    "cache_hits": stats.cache_hits,
                    "cache_misses": stats.cache_misses,
                    "hit_rate_percent": stats.hit_rate,
                    "total_cost_saved": stats.total_cost_saved,
                    "avg_response_time_ms": stats.avg_response_time * 1000,
                    "storage_usage_mb": stats.storage_usage_mb
                },
                "cost_savings": {
                    "total_saved": stats.total_cost_saved,
                    "estimated_monthly_savings": stats.total_cost_saved * 30 / 7 if stats.total_requests > 0 else 0,
                    "savings_per_request": stats.total_cost_saved / stats.total_requests if stats.total_requests > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance by removing old entries"""
        if not self.cache_manager:
            return {"error": "Caching not enabled"}
        
        try:
            optimization_results = await self.cache_manager.optimize_cache()
            return {
                "success": True,
                "optimization_results": optimization_results,
                "message": f"Cache optimized: {optimization_results.get('removed_expired', 0)} expired entries removed"
            }
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"error": str(e)}
    
    async def invalidate_user_cache(self, user_id: str) -> Dict[str, Any]:
        """Invalidate all cache entries for a specific user"""
        if not self.cache_manager:
            return {"error": "Caching not enabled"}
        
        try:
            invalidated_count = await self.cache_manager.invalidate_cache(user_id=user_id)
            return {
                "success": True,
                "invalidated_entries": invalidated_count,
                "message": f"Invalidated {invalidated_count} cache entries for user {user_id}"
            }
        except Exception as e:
            logger.error(f"Cache invalidation failed for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_cache_efficiency_report(self, user: User, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive cache efficiency report"""
        try:
            # Get cache stats
            cache_stats = await self.get_cache_stats(str(user.id))
            
            # Get user's AI usage for comparison
            analytics = await self.get_usage_analytics(user, days)
            
            # Calculate efficiency metrics
            total_requests = analytics.get("total_requests", 0)
            total_cost = analytics.get("total_cost", 0)
            
            if cache_stats.get("stats"):
                cache_hit_rate = cache_stats["stats"]["hit_rate_percent"]
                cost_saved = cache_stats["stats"]["total_cost_saved"]
                
                # Calculate what cost would have been without caching
                estimated_cost_without_cache = total_cost + cost_saved
                cost_efficiency = (cost_saved / estimated_cost_without_cache * 100) if estimated_cost_without_cache > 0 else 0
                
                return {
                    "user_id": str(user.id),
                    "period_days": days,
                    "cache_performance": {
                        "hit_rate_percent": cache_hit_rate,
                        "cost_efficiency_percent": round(cost_efficiency, 2),
                        "total_cost_saved": cost_saved,
                        "estimated_without_cache": round(estimated_cost_without_cache, 4)
                    },
                    "usage_comparison": {
                        "actual_cost": total_cost,
                        "requests_served_from_cache": cache_stats["stats"]["cache_hits"],
                        "requests_requiring_ai": cache_stats["stats"]["cache_misses"],
                        "cache_to_ai_ratio": round(
                            cache_stats["stats"]["cache_hits"] / max(cache_stats["stats"]["cache_misses"], 1), 2
                        )
                    },
                    "recommendations": self._generate_cache_recommendations(cache_stats["stats"], total_requests)
                }
            else:
                return {
                    "user_id": str(user.id),
                    "period_days": days,
                    "cache_performance": {"message": "No cache data available"},
                    "recommendations": ["Enable caching to reduce AI costs"]
                }
                
        except Exception as e:
            logger.error(f"Failed to generate cache efficiency report: {e}")
            return {"error": str(e)}
    
    def _generate_cache_recommendations(self, cache_stats: Dict[str, Any], total_requests: int) -> List[str]:
        """Generate cache optimization recommendations"""
        recommendations = []
        
        hit_rate = cache_stats.get("hit_rate_percent", 0)
        
        if hit_rate < 30:
            recommendations.append("Low cache hit rate - consider using more specific prompts for better cache matching")
        elif hit_rate < 50:
            recommendations.append("Moderate cache hit rate - review prompt patterns to increase reusability")
        elif hit_rate > 80:
            recommendations.append("Excellent cache performance - consider increasing cache TTL for popular components")
        
        storage_mb = cache_stats.get("storage_usage_mb", 0)
        if storage_mb > 100:
            recommendations.append("High cache storage usage - consider running cache optimization")
        
        if total_requests > 100 and hit_rate < 20:
            recommendations.append("Many unique requests - consider using templates or component libraries")
        
        if not recommendations:
            recommendations.append("Cache performance is good - continue current usage patterns")
        
        return recommendations