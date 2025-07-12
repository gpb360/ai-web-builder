"""
AI Router - Intelligent model selection and cost optimization
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import (
    AIRequest, AIResponse, ModelType, TaskType, ComplexityLevel, UserTier,
    MODEL_COSTS, MODEL_CAPABILITIES
)
from config import settings

logger = logging.getLogger(__name__)

@dataclass
class ModelSelection:
    """Model selection result"""
    model: ModelType
    confidence: float  # 0-1 score for selection confidence
    reason: str
    estimated_cost: float
    fallbacks: List[ModelType]

class AIRouter:
    """Intelligent AI model router with cost optimization"""
    
    def __init__(self):
        self.selection_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[ModelType, Dict[str, float]] = {}
        self._initialize_performance_metrics()
    
    def _initialize_performance_metrics(self):
        """Initialize default performance metrics for each model"""
        for model in ModelType:
            self.performance_metrics[model] = {
                "success_rate": 0.95,  # Default success rate
                "avg_quality": 0.8,    # Default quality score
                "avg_response_time": 5.0,  # Default response time in seconds
                "cost_efficiency": 1.0,    # Cost vs quality ratio
                "last_updated": datetime.utcnow().timestamp()
            }
    
    def select_model(self, request: AIRequest) -> ModelSelection:
        """
        Select the optimal AI model for a given request with intelligent optimization
        
        Args:
            request: AI request with task details
            
        Returns:
            ModelSelection with chosen model and rationale
        """
        logger.info(f"Selecting model for task: {request.task_type}, complexity: {request.complexity}, tier: {request.user_tier}")
        
        # Apply smart optimizations based on request patterns
        optimized_request = self._apply_smart_optimizations(request)
        
        # Get candidate models based on task requirements
        candidates = self._get_candidate_models(optimized_request)
        
        # Apply load balancing if multiple similar-scoring models exist
        scored_models = []
        for model in candidates:
            score = self._score_model(model, optimized_request)
            # Apply load balancing factor
            load_factor = self._get_load_balancing_factor(model)
            adjusted_score = score * load_factor
            scored_models.append((model, adjusted_score, score))
        
        # Sort by adjusted score (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_models:
            # Smart fallback selection based on user tier
            fallback_model = self._get_smart_fallback(optimized_request)
            logger.warning(f"No suitable models found, falling back to {fallback_model.value}")
            return ModelSelection(
                model=fallback_model,
                confidence=0.5,
                reason="Smart fallback selection - no optimal candidates found",
                estimated_cost=self._estimate_cost(fallback_model, optimized_request),
                fallbacks=[ModelType.DEEPSEEK_V3]
            )
        
        # Select the best model
        best_model, adjusted_score, original_score = scored_models[0]
        fallbacks = [model for model, _, _ in scored_models[1:3]]  # Top 2 alternatives
        
        # Calculate confidence with load balancing consideration
        confidence = min(original_score / 100.0, 1.0)
        if len(scored_models) > 1:
            second_best_score = scored_models[1][2]  # Use original score for confidence
            score_gap = (original_score - second_best_score) / 100.0
            confidence = min(confidence, 0.5 + score_gap)
        
        estimated_cost = self._estimate_cost(best_model, optimized_request)
        reason = self._explain_selection(best_model, optimized_request, original_score)
        
        selection = ModelSelection(
            model=best_model,
            confidence=confidence,
            reason=reason,
            estimated_cost=estimated_cost,
            fallbacks=fallbacks
        )
        
        # Log selection for future optimization
        self._log_selection(optimized_request, selection)
        
        return selection
    
    def _get_candidate_models(self, request: AIRequest) -> List[ModelType]:
        """Get list of candidate models based on request requirements"""
        candidates = []
        
        for model, capabilities in MODEL_CAPABILITIES.items():
            # Check if model can handle the complexity
            if capabilities["max_complexity"] < request.complexity:
                continue
            
            # Check if vision is required
            if request.requires_vision and not capabilities.get("vision_capable", False):
                continue
            
            # Check if model is good for this task type
            if request.task_type in capabilities["strengths"]:
                candidates.append(model)
            elif request.complexity <= capabilities["max_complexity"]:
                candidates.append(model)
        
        return candidates
    
    def _score_model(self, model: ModelType, request: AIRequest) -> float:
        """
        Score a model for a given request (0-100)
        
        Factors:
        - Cost efficiency (40%)
        - Task suitability (30%) 
        - Historical performance (20%)
        - User tier appropriateness (10%)
        """
        score = 0.0
        
        # Cost efficiency (40% weight)
        cost_score = self._calculate_cost_score(model, request)
        score += cost_score * 0.4
        
        # Task suitability (30% weight)
        suitability_score = self._calculate_suitability_score(model, request)
        score += suitability_score * 0.3
        
        # Historical performance (20% weight)
        performance_score = self._calculate_performance_score(model, request)
        score += performance_score * 0.2
        
        # User tier appropriateness (10% weight)
        tier_score = self._calculate_tier_score(model, request)
        score += tier_score * 0.1
        
        return score
    
    def _calculate_cost_score(self, model: ModelType, request: AIRequest) -> float:
        """Calculate cost efficiency score (0-100)"""
        estimated_cost = self._estimate_cost(model, request)
        
        # If user has max cost limit, prioritize staying under it
        if request.max_cost and estimated_cost > request.max_cost:
            return 0.0
        
        # Score based on cost efficiency (lower cost = higher score)
        # DeepSeek gets 100, GPT-4 gets lower scores
        max_cost = 0.10  # $0.10 as reference expensive cost
        cost_score = max(0, 100 - (estimated_cost / max_cost * 100))
        
        return min(100, cost_score)
    
    def _calculate_suitability_score(self, model: ModelType, request: AIRequest) -> float:
        """Calculate task suitability score (0-100)"""
        capabilities = MODEL_CAPABILITIES[model]
        
        # Base suitability
        if request.task_type in capabilities["strengths"]:
            base_score = 90
        elif request.complexity <= capabilities["max_complexity"]:
            base_score = 70
        else:
            base_score = 30
        
        # Adjust for complexity match
        complexity_match = min(1.0, capabilities["max_complexity"] / request.complexity)
        complexity_bonus = complexity_match * 10
        
        # Quality tier bonus
        quality_tiers = {"basic": 0, "good": 5, "high": 10, "premium": 15, "enterprise": 20}
        quality_bonus = quality_tiers.get(capabilities["quality_tier"], 0)
        
        return min(100, base_score + complexity_bonus + quality_bonus)
    
    def _calculate_performance_score(self, model: ModelType, request: AIRequest) -> float:
        """Calculate historical performance score (0-100)"""
        metrics = self.performance_metrics.get(model, {})
        
        success_rate = metrics.get("success_rate", 0.95)
        avg_quality = metrics.get("avg_quality", 0.8)
        cost_efficiency = metrics.get("cost_efficiency", 1.0)
        
        # Combine metrics
        performance_score = (
            success_rate * 40 +      # 40% weight on reliability
            avg_quality * 40 +       # 40% weight on quality
            min(cost_efficiency, 2.0) * 10  # 20% weight on cost efficiency
        )
        
        return min(100, performance_score * 100)
    
    def _calculate_tier_score(self, model: ModelType, request: AIRequest) -> float:
        """Calculate user tier appropriateness score (0-100)"""
        tier_model_preference = {
            UserTier.FREE.value: [ModelType.DEEPSEEK_V3, ModelType.GEMINI_FLASH],
            UserTier.CREATOR.value: [ModelType.GEMINI_FLASH, ModelType.GEMINI_PRO, ModelType.DEEPSEEK_V3],
            UserTier.BUSINESS.value: [ModelType.GEMINI_PRO, ModelType.CLAUDE_SONNET, ModelType.GEMINI_FLASH],
            UserTier.AGENCY.value: [ModelType.CLAUDE_SONNET, ModelType.GPT4_TURBO, ModelType.GEMINI_PRO]
        }
        
        preferred_models = tier_model_preference.get(request.user_tier, [])
        
        if model in preferred_models:
            # Higher score for earlier models in preference list
            index = preferred_models.index(model)
            return 100 - (index * 20)  # 100, 80, 60, etc.
        else:
            # Penalty for using expensive models on lower tiers
            if request.user_tier == UserTier.FREE.value and model in [ModelType.CLAUDE_SONNET, ModelType.GPT4_TURBO]:
                return 10
            return 50  # Neutral score
    
    def _estimate_cost(self, model: ModelType, request: AIRequest) -> float:
        """Estimate cost for a request with given model"""
        # Estimate token counts based on content length and task type
        input_tokens = len(request.content.split()) * 1.3  # Rough estimation
        
        # Output tokens vary by task type
        output_multipliers = {
            TaskType.CODE_GENERATION.value: 2.0,
            TaskType.CONTENT_WRITING.value: 1.5,
            TaskType.ANALYSIS.value: 1.2,
            TaskType.OPTIMIZATION.value: 1.3,
            TaskType.COMPONENT_GENERATION.value: 2.5,
            TaskType.CAMPAIGN_ANALYSIS.value: 1.8
        }
        
        output_multiplier = output_multipliers.get(request.task_type, 1.0)
        output_tokens = input_tokens * output_multiplier
        
        # Calculate cost
        model_costs = MODEL_COSTS[model]
        return model_costs.calculate_cost(
            int(input_tokens), 
            int(output_tokens),
            1 if request.requires_vision else 0
        )
    
    def _explain_selection(self, model: ModelType, request: AIRequest, score: float) -> str:
        """Generate human-readable explanation for model selection"""
        cost = self._estimate_cost(model, request)
        capabilities = MODEL_CAPABILITIES[model]
        
        reasons = []
        
        # Cost reasoning
        if cost < 0.001:
            reasons.append("ultra-low cost")
        elif cost < 0.01:
            reasons.append("cost-effective")
        elif cost < 0.05:
            reasons.append("balanced cost/quality")
        else:
            reasons.append("premium quality justified")
        
        # Task suitability
        if request.task_type in capabilities["strengths"]:
            reasons.append(f"optimized for {request.task_type}")
        
        # Complexity handling
        if request.complexity <= capabilities["max_complexity"]:
            reasons.append("complexity match")
        
        # User tier appropriateness
        tier_appropriate = {
            UserTier.FREE.value: model in [ModelType.DEEPSEEK_V3, ModelType.GEMINI_FLASH],
            UserTier.CREATOR.value: model in [ModelType.GEMINI_FLASH, ModelType.GEMINI_PRO],
            UserTier.BUSINESS.value: model in [ModelType.GEMINI_PRO, ModelType.CLAUDE_SONNET],
            UserTier.AGENCY.value: model in [ModelType.CLAUDE_SONNET, ModelType.GPT4_TURBO]
        }
        
        if tier_appropriate.get(request.user_tier, False):
            reasons.append(f"tier-appropriate for {request.user_tier}")
        
        return f"Selected {model.value} (score: {score:.1f}) - {', '.join(reasons)}"
    
    def _log_selection(self, request: AIRequest, selection: ModelSelection):
        """Log selection for future optimization"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "task_type": request.task_type,
            "complexity": request.complexity,
            "user_tier": request.user_tier,
            "selected_model": selection.model.value,
            "confidence": selection.confidence,
            "estimated_cost": selection.estimated_cost,
            "content_length": len(request.content)
        }
        
        self.selection_history.append(log_entry)
        
        # Keep only last 1000 selections to prevent memory bloat
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-1000:]
    
    def update_performance_metrics(self, response: AIResponse, user_feedback: Optional[Dict[str, Any]] = None):
        """Update performance metrics based on actual results"""
        model = response.model_used
        
        # Update basic metrics
        metrics = self.performance_metrics[model]
        
        # Update quality score if provided
        if response.quality_score is not None:
            current_quality = metrics["avg_quality"]
            metrics["avg_quality"] = (current_quality * 0.9) + (response.quality_score * 0.1)
        
        # Update response time
        if response.processing_time is not None:
            current_time = metrics["avg_response_time"]
            metrics["avg_response_time"] = (current_time * 0.9) + (response.processing_time * 0.1)
        
        # Update cost efficiency (lower cost per token = higher efficiency)
        total_tokens = response.input_tokens + response.output_tokens
        if total_tokens > 0:
            cost_per_token = response.cost / total_tokens
            efficiency = 1.0 / max(cost_per_token, 0.000001)  # Avoid division by zero
            current_efficiency = metrics["cost_efficiency"]
            metrics["cost_efficiency"] = (current_efficiency * 0.9) + (efficiency * 0.1)
        
        # Update success rate based on user feedback
        if user_feedback:
            success = user_feedback.get("success", True)
            current_success_rate = metrics["success_rate"]
            new_success = 1.0 if success else 0.0
            metrics["success_rate"] = (current_success_rate * 0.95) + (new_success * 0.05)
        
        metrics["last_updated"] = datetime.utcnow().timestamp()
        
        logger.info(f"Updated performance metrics for {model.value}: quality={metrics['avg_quality']:.3f}, "
                   f"success_rate={metrics['success_rate']:.3f}, efficiency={metrics['cost_efficiency']:.3f}")
    
    def get_model_recommendations(self, task_type: str, user_tier: str) -> List[ModelType]:
        """Get recommended models for a task type and user tier"""
        # Mock request for analysis
        mock_request = AIRequest(
            task_type=task_type,
            complexity=5,  # Medium complexity
            content="Sample content for analysis",
            user_tier=user_tier
        )
        
        candidates = self._get_candidate_models(mock_request)
        scored_models = [(model, self._score_model(model, mock_request)) for model in candidates]
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        return [model for model, _ in scored_models[:3]]  # Top 3 recommendations
    
    def get_cost_analysis(self, content_length: int, task_type: str) -> Dict[ModelType, float]:
        """Get cost analysis for different models"""
        mock_request = AIRequest(
            task_type=task_type,
            complexity=5,
            content="x " * content_length,  # Mock content of specified length
            user_tier=UserTier.BUSINESS.value
        )
        
        cost_analysis = {}
        for model in ModelType:
            cost_analysis[model] = self._estimate_cost(model, mock_request)
        
        return cost_analysis
    
    def _apply_smart_optimizations(self, request: AIRequest) -> AIRequest:
        """Apply intelligent optimizations to the request based on patterns"""
        optimized_request = AIRequest(
            task_type=request.task_type,
            complexity=request.complexity,
            content=request.content,
            user_tier=request.user_tier,
            max_cost=request.max_cost,
            requires_vision=request.requires_vision,
            context_length=request.context_length
        )
        
        # Smart complexity adjustment based on content analysis
        content_length = len(request.content)
        
        # Reduce complexity for very short requests (likely simple tasks)
        if content_length < 50 and request.complexity > 3:
            optimized_request.complexity = max(2, request.complexity - 1)
            logger.info(f"Reduced complexity from {request.complexity} to {optimized_request.complexity} for short content")
        
        # Increase complexity for very long, detailed requests
        elif content_length > 2000 and request.complexity < 6:
            optimized_request.complexity = min(8, request.complexity + 1)
            logger.info(f"Increased complexity from {request.complexity} to {optimized_request.complexity} for detailed content")
        
        # Smart task type optimization based on content patterns
        content_lower = request.content.lower()
        
        # Detect if this is actually a code-related task
        code_indicators = ['component', 'function', 'react', 'javascript', 'typescript', 'css', 'html', 'api']
        if any(indicator in content_lower for indicator in code_indicators):
            if request.task_type in ['content_writing', 'analysis']:
                optimized_request.task_type = 'code_generation'
                logger.info(f"Optimized task type from {request.task_type} to code_generation")
        
        # Detect analysis requests masquerading as content writing
        analysis_indicators = ['analyze', 'review', 'compare', 'evaluate', 'assess', 'audit']
        if any(indicator in content_lower for indicator in analysis_indicators):
            if request.task_type == 'content_writing':
                optimized_request.task_type = 'analysis'
                logger.info(f"Optimized task type from {request.task_type} to analysis")
        
        return optimized_request
    
    def _get_load_balancing_factor(self, model: ModelType) -> float:
        """Get load balancing factor to distribute load across similar models"""
        # Simple load balancing based on recent usage
        recent_selections = [
            entry for entry in self.selection_history[-100:]  # Last 100 selections
            if entry["selected_model"] == model.value
        ]
        
        usage_count = len(recent_selections)
        
        # Apply gentle load balancing - reduce score if heavily used recently
        if usage_count > 20:  # More than 20% of recent selections
            return 0.9  # Slight penalty
        elif usage_count > 30:  # More than 30% of recent selections
            return 0.8  # Moderate penalty
        elif usage_count > 40:  # More than 40% of recent selections
            return 0.7  # Higher penalty to encourage diversity
        else:
            return 1.0  # No penalty
    
    def _get_smart_fallback(self, request: AIRequest) -> ModelType:
        """Get intelligent fallback model based on user tier and request"""
        tier_fallbacks = {
            UserTier.FREE.value: ModelType.DEEPSEEK_V3,
            UserTier.CREATOR.value: ModelType.GEMINI_FLASH,
            UserTier.BUSINESS.value: ModelType.GEMINI_PRO,
            UserTier.AGENCY.value: ModelType.CLAUDE_SONNET
        }
        
        preferred_fallback = tier_fallbacks.get(request.user_tier, ModelType.DEEPSEEK_V3)
        
        # Additional logic for vision requirements
        if request.requires_vision:
            return ModelType.GPT4_VISION
        
        # For high complexity, ensure fallback can handle it
        if request.complexity > 7:
            high_complexity_models = [ModelType.CLAUDE_SONNET, ModelType.GPT4_TURBO]
            if preferred_fallback not in high_complexity_models:
                return ModelType.CLAUDE_SONNET
        
        return preferred_fallback
    
    def get_selection_analytics(self) -> Dict[str, Any]:
        """Get analytics on model selection patterns"""
        if not self.selection_history:
            return {"message": "No selection history available"}
        
        recent_selections = self.selection_history[-100:]  # Last 100 selections
        
        # Model distribution
        model_counts = {}
        task_type_counts = {}
        user_tier_counts = {}
        
        for selection in recent_selections:
            model = selection["selected_model"]
            task = selection["task_type"]
            tier = selection["user_tier"]
            
            model_counts[model] = model_counts.get(model, 0) + 1
            task_type_counts[task] = task_type_counts.get(task, 0) + 1
            user_tier_counts[tier] = user_tier_counts.get(tier, 0) + 1
        
        # Cost analysis
        total_estimated_cost = sum(s["estimated_cost"] for s in recent_selections)
        avg_cost = total_estimated_cost / len(recent_selections) if recent_selections else 0
        
        # Confidence analysis
        avg_confidence = sum(s["confidence"] for s in recent_selections) / len(recent_selections) if recent_selections else 0
        
        return {
            "total_selections": len(recent_selections),
            "model_distribution": model_counts,
            "task_type_distribution": task_type_counts,
            "user_tier_distribution": user_tier_counts,
            "avg_estimated_cost": avg_cost,
            "total_estimated_cost": total_estimated_cost,
            "avg_confidence": avg_confidence,
            "cost_efficiency": {
                "most_used_model": max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None,
                "highest_avg_cost": max(MODEL_COSTS.items(), key=lambda x: x[1].output_cost)[0].value,
                "lowest_avg_cost": min(MODEL_COSTS.items(), key=lambda x: x[1].output_cost)[0].value
            }
        }