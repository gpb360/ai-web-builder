"""
Real-time AI cost tracking and budget management system
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import User, AIUsage
from .models import AIRequest, AIResponse, ModelType

logger = logging.getLogger(__name__)

@dataclass
class CostAlert:
    """Cost alert configuration"""
    user_id: str
    alert_type: str  # 'budget_exceeded', 'budget_warning', 'anomaly'
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'

@dataclass
class UsageSummary:
    """Usage summary for a time period"""
    total_cost: float
    total_requests: int
    avg_cost_per_request: float
    model_breakdown: Dict[str, Dict[str, float]]
    task_breakdown: Dict[str, Dict[str, float]]
    daily_trend: List[Dict[str, Any]]
    
@dataclass
class BudgetStatus:
    """User budget status"""
    user_id: str
    tier: str
    monthly_limit: float
    current_usage: float
    remaining_budget: float
    percentage_used: float
    days_remaining: int
    projected_overage: Optional[float]
    
class CostTracker:
    """Real-time cost tracking and budget management"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.alert_thresholds = {
            'warning': 0.75,  # 75% of budget
            'critical': 0.90,  # 90% of budget
            'exceeded': 1.0   # 100% of budget
        }
        
        # Subscription limits (from config)
        self.subscription_limits = {
            'free': {'monthly_budget': 1.00},      # $1/month
            'creator': {'monthly_budget': 8.82},   # $49 * 18% margin
            'business': {'monthly_budget': 23.84}, # $149 * 16% margin  
            'agency': {'monthly_budget': 131.67}   # $399 * 33% margin
        }
    
    async def track_request_cost(
        self,
        user: User,
        request: AIRequest,
        response: AIResponse,
        selection_metadata: Optional[Dict[str, Any]] = None
    ) -> CostAlert:
        """
        Track cost for an AI request and check for budget alerts
        
        Args:
            user: User making the request
            request: Original AI request
            response: AI response with cost information
            selection_metadata: Additional selection metadata
            
        Returns:
            CostAlert if budget thresholds are exceeded, None otherwise
        """
        # Record usage in database
        await self._record_usage(user, request, response, selection_metadata)
        
        # Update real-time cost cache
        if self.redis:
            await self._update_cost_cache(user, response.cost)
        
        # Check budget status and generate alerts
        budget_status = await self.get_budget_status(user)
        alert = await self._check_budget_alerts(user, budget_status)
        
        # Log cost tracking
        logger.info(
            f"Cost tracked for user {user.id}: ${response.cost:.6f} "
            f"({budget_status.percentage_used:.1f}% of budget used)"
        )
        
        return alert
    
    async def _record_usage(
        self,
        user: User,
        request: AIRequest,
        response: AIResponse,
        selection_metadata: Optional[Dict[str, Any]]
    ):
        """Record usage in database"""
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
                'complexity': request.complexity,
                'content_length': len(request.content),
                'requires_vision': request.requires_vision,
                'selection_metadata': selection_metadata or {},
                'timestamp': response.timestamp.isoformat() if response.timestamp else None
            }
        )
        
        self.db.add(usage_record)
        await self.db.commit()
    
    async def _update_cost_cache(self, user: User, cost: float):
        """Update real-time cost cache in Redis"""
        try:
            now = datetime.utcnow()
            
            # Daily cache
            daily_key = f"cost:daily:{user.id}:{now.strftime('%Y-%m-%d')}"
            await self.redis.incrbyfloat(daily_key, cost)
            await self.redis.expire(daily_key, 86400 * 7)  # Keep for 7 days
            
            # Monthly cache
            monthly_key = f"cost:monthly:{user.id}:{now.strftime('%Y-%m')}"
            await self.redis.incrbyfloat(monthly_key, cost)
            await self.redis.expire(monthly_key, 86400 * 32)  # Keep for 32 days
            
            # Hourly cache for real-time monitoring
            hourly_key = f"cost:hourly:{user.id}:{now.strftime('%Y-%m-%d-%H')}"
            await self.redis.incrbyfloat(hourly_key, cost)
            await self.redis.expire(hourly_key, 3600 * 24)  # Keep for 24 hours
            
            # Request count cache
            request_key = f"requests:daily:{user.id}:{now.strftime('%Y-%m-%d')}"
            await self.redis.incr(request_key)
            await self.redis.expire(request_key, 86400 * 7)
            
        except Exception as e:
            logger.warning(f"Failed to update cost cache: {e}")
    
    async def get_budget_status(self, user: User) -> BudgetStatus:
        """Get current budget status for user"""
        # Get monthly limit based on subscription tier
        tier_limits = self.subscription_limits.get(
            user.subscription_tier.lower(), 
            self.subscription_limits['free']
        )
        monthly_limit = tier_limits['monthly_budget']
        
        # Get current month usage
        current_usage = await self._get_monthly_usage(user)
        
        # Calculate remaining budget and percentage
        remaining_budget = max(0, monthly_limit - current_usage)
        percentage_used = (current_usage / monthly_limit) * 100 if monthly_limit > 0 else 0
        
        # Calculate days remaining in month
        now = datetime.utcnow()
        next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        days_remaining = (next_month - now).days
        
        # Project potential overage
        projected_overage = None
        if days_remaining > 0 and current_usage > 0:
            # Get daily average for last 7 days
            daily_avg = await self._get_daily_average_cost(user, 7)
            projected_monthly = daily_avg * days_remaining + current_usage
            if projected_monthly > monthly_limit:
                projected_overage = projected_monthly - monthly_limit
        
        return BudgetStatus(
            user_id=str(user.id),
            tier=user.subscription_tier,
            monthly_limit=monthly_limit,
            current_usage=current_usage,
            remaining_budget=remaining_budget,
            percentage_used=percentage_used,
            days_remaining=days_remaining,
            projected_overage=projected_overage
        )
    
    async def _get_monthly_usage(self, user: User) -> float:
        """Get user's current month usage from database"""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.sum(AIUsage.cost)).where(
                and_(
                    AIUsage.user_id == user.id,
                    AIUsage.created_at >= month_start
                )
            )
        )
        
        total_cost = result.scalar_one_or_none()
        return float(total_cost) if total_cost else 0.0
    
    async def _get_daily_average_cost(self, user: User, days: int) -> float:
        """Get daily average cost for last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        result = await self.db.execute(
            select(func.sum(AIUsage.cost)).where(
                and_(
                    AIUsage.user_id == user.id,
                    AIUsage.created_at >= start_date,
                    AIUsage.created_at <= end_date
                )
            )
        )
        
        total_cost = result.scalar_one_or_none()
        if not total_cost:
            return 0.0
        
        return float(total_cost) / days
    
    async def _check_budget_alerts(self, user: User, budget_status: BudgetStatus) -> Optional[CostAlert]:
        """Check if budget alerts should be triggered"""
        percentage = budget_status.percentage_used / 100
        
        # Generate appropriate alert
        if percentage >= self.alert_thresholds['exceeded']:
            return CostAlert(
                user_id=budget_status.user_id,
                alert_type='budget_exceeded',
                threshold=budget_status.monthly_limit,
                current_value=budget_status.current_usage,
                message=f"Budget exceeded! Used ${budget_status.current_usage:.2f} of ${budget_status.monthly_limit:.2f}",
                timestamp=datetime.utcnow(),
                severity='critical'
            )
        elif percentage >= self.alert_thresholds['critical']:
            return CostAlert(
                user_id=budget_status.user_id,
                alert_type='budget_warning',
                threshold=budget_status.monthly_limit * self.alert_thresholds['critical'],
                current_value=budget_status.current_usage,
                message=f"Budget warning: {percentage:.1%} used (${budget_status.current_usage:.2f}/${budget_status.monthly_limit:.2f})",
                timestamp=datetime.utcnow(),
                severity='high'
            )
        elif percentage >= self.alert_thresholds['warning']:
            return CostAlert(
                user_id=budget_status.user_id,
                alert_type='budget_warning',
                threshold=budget_status.monthly_limit * self.alert_thresholds['warning'],
                current_value=budget_status.current_usage,
                message=f"Budget alert: {percentage:.1%} used (${budget_status.current_usage:.2f}/${budget_status.monthly_limit:.2f})",
                timestamp=datetime.utcnow(),
                severity='medium'
            )
        
        # Check for projected overage
        if budget_status.projected_overage and budget_status.projected_overage > 0:
            return CostAlert(
                user_id=budget_status.user_id,
                alert_type='projection_warning',
                threshold=budget_status.monthly_limit,
                current_value=budget_status.current_usage + budget_status.projected_overage,
                message=f"Projected overage: ${budget_status.projected_overage:.2f} based on current usage trend",
                timestamp=datetime.utcnow(),
                severity='medium'
            )
        
        return None
    
    async def get_usage_summary(self, user: User, days: int = 30) -> UsageSummary:
        """Get comprehensive usage summary for user"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage records
        result = await self.db.execute(
            select(AIUsage).where(
                and_(
                    AIUsage.user_id == user.id,
                    AIUsage.created_at >= start_date
                )
            ).order_by(AIUsage.created_at.desc())
        )
        
        usage_records = result.scalars().all()
        
        if not usage_records:
            return UsageSummary(
                total_cost=0.0,
                total_requests=0,
                avg_cost_per_request=0.0,
                model_breakdown={},
                task_breakdown={},
                daily_trend=[]
            )
        
        # Calculate totals
        total_cost = sum(record.cost for record in usage_records)
        total_requests = len(usage_records)
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        
        # Model breakdown
        model_breakdown = {}
        for record in usage_records:
            model = record.model_used
            if model not in model_breakdown:
                model_breakdown[model] = {'count': 0, 'cost': 0.0, 'avg_cost': 0.0}
            model_breakdown[model]['count'] += 1
            model_breakdown[model]['cost'] += record.cost
        
        # Calculate averages
        for model_data in model_breakdown.values():
            model_data['avg_cost'] = model_data['cost'] / model_data['count']
        
        # Task breakdown
        task_breakdown = {}
        for record in usage_records:
            task = record.task_type
            if task not in task_breakdown:
                task_breakdown[task] = {'count': 0, 'cost': 0.0, 'avg_cost': 0.0}
            task_breakdown[task]['count'] += 1
            task_breakdown[task]['cost'] += record.cost
        
        # Calculate averages
        for task_data in task_breakdown.values():
            task_data['avg_cost'] = task_data['cost'] / task_data['count']
        
        # Daily trend
        daily_trend = await self._calculate_daily_trend(usage_records, start_date, end_date)
        
        return UsageSummary(
            total_cost=total_cost,
            total_requests=total_requests,
            avg_cost_per_request=avg_cost,
            model_breakdown=model_breakdown,
            task_breakdown=task_breakdown,
            daily_trend=daily_trend
        )
    
    async def _calculate_daily_trend(self, usage_records: List[AIUsage], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Calculate daily usage trend"""
        daily_data = {}
        
        # Initialize all days with zero
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            daily_data[current_date.isoformat()] = {'cost': 0.0, 'requests': 0}
            current_date += timedelta(days=1)
        
        # Aggregate usage by day
        for record in usage_records:
            day_key = record.created_at.date().isoformat()
            if day_key in daily_data:
                daily_data[day_key]['cost'] += record.cost
                daily_data[day_key]['requests'] += 1
        
        # Convert to list format
        trend = []
        for date_str, data in sorted(daily_data.items()):
            trend.append({
                'date': date_str,
                'cost': data['cost'],
                'requests': data['requests'],
                'avg_cost_per_request': data['cost'] / data['requests'] if data['requests'] > 0 else 0
            })
        
        return trend
    
    async def get_real_time_metrics(self, user: User) -> Dict[str, Any]:
        """Get real-time cost metrics from cache"""
        if not self.redis:
            return {'error': 'Redis not available for real-time metrics'}
        
        try:
            now = datetime.utcnow()
            
            # Current hour cost
            hourly_key = f"cost:hourly:{user.id}:{now.strftime('%Y-%m-%d-%H')}"
            hourly_cost = await self.redis.get(hourly_key)
            hourly_cost = float(hourly_cost) if hourly_cost else 0.0
            
            # Today's cost
            daily_key = f"cost:daily:{user.id}:{now.strftime('%Y-%m-%d')}"
            daily_cost = await self.redis.get(daily_key)
            daily_cost = float(daily_cost) if daily_cost else 0.0
            
            # This month's cost
            monthly_key = f"cost:monthly:{user.id}:{now.strftime('%Y-%m')}"
            monthly_cost = await self.redis.get(monthly_key)
            monthly_cost = float(monthly_cost) if monthly_cost else 0.0
            
            # Today's requests
            request_key = f"requests:daily:{user.id}:{now.strftime('%Y-%m-%d')}"
            daily_requests = await self.redis.get(request_key)
            daily_requests = int(daily_requests) if daily_requests else 0
            
            return {
                'current_hour_cost': hourly_cost,
                'today_cost': daily_cost,
                'month_cost': monthly_cost,
                'today_requests': daily_requests,
                'avg_cost_per_request_today': daily_cost / daily_requests if daily_requests > 0 else 0,
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {'error': str(e)}
    
    async def check_request_budget(self, user: User, estimated_cost: float) -> Dict[str, Any]:
        """Check if request can proceed within budget"""
        budget_status = await self.get_budget_status(user)
        
        # Check if request would exceed budget
        would_exceed_budget = (budget_status.current_usage + estimated_cost) > budget_status.monthly_limit
        
        # Calculate remaining requests at this cost level
        remaining_requests = 0
        if estimated_cost > 0:
            remaining_requests = int(budget_status.remaining_budget // estimated_cost)
        
        return {
            'can_proceed': not would_exceed_budget,
            'current_usage': budget_status.current_usage,
            'monthly_limit': budget_status.monthly_limit,
            'remaining_budget': budget_status.remaining_budget,
            'estimated_cost': estimated_cost,
            'after_request_usage': budget_status.current_usage + estimated_cost,
            'remaining_requests_at_this_cost': remaining_requests,
            'percentage_used': budget_status.percentage_used,
            'would_exceed': would_exceed_budget
        }
    
    async def get_cost_optimization_recommendations(self, user: User) -> List[Dict[str, Any]]:
        """Get personalized cost optimization recommendations"""
        summary = await self.get_usage_summary(user, 30)
        recommendations = []
        
        if summary.total_cost == 0:
            return recommendations
        
        # Analyze model usage for expensive patterns
        for model, data in summary.model_breakdown.items():
            cost_percentage = (data['cost'] / summary.total_cost) * 100
            
            # Recommend switching from expensive models
            if cost_percentage > 30 and model in ['gpt-4-turbo', 'claude-3.5-sonnet']:
                potential_savings = data['cost'] * 0.8  # Estimate 80% savings
                recommendations.append({
                    'type': 'model_optimization',
                    'priority': 'high',
                    'title': f'Switch from {model} to cost-effective alternatives',
                    'description': f'{model} accounts for {cost_percentage:.1f}% of your costs. Consider Gemini Pro or DeepSeek for similar quality.',
                    'potential_monthly_savings': potential_savings,
                    'impact': 'high'
                })
        
        # Analyze task patterns
        for task, data in summary.task_breakdown.items():
            cost_percentage = (data['cost'] / summary.total_cost) * 100
            
            if cost_percentage > 40:
                recommendations.append({
                    'type': 'workflow_optimization',
                    'priority': 'medium',
                    'title': f'Optimize {task} workflow',
                    'description': f'{task} represents {cost_percentage:.1f}% of your AI costs. Consider batching requests or using templates.',
                    'potential_monthly_savings': data['cost'] * 0.3,
                    'impact': 'medium'
                })
        
        # Budget tier recommendations
        budget_status = await self.get_budget_status(user)
        if budget_status.percentage_used > 85:
            recommendations.append({
                'type': 'budget_management',
                'priority': 'high',
                'title': 'Consider upgrading your plan',
                'description': f"You've used {budget_status.percentage_used:.1f}% of your monthly budget. Upgrading provides more AI credits and better models.",
                'potential_monthly_savings': 0,
                'impact': 'high'
            })
        
        return recommendations