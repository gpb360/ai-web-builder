"""
Database utility functions for common operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from database.models import (
    User, UserUsage, Campaign, CampaignComponent, 
    AIGeneration, AICostTracking, PlatformIntegration
)
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

class DatabaseUtils:
    """Utility class for common database operations"""
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await session.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_usage_for_month(
        session: AsyncSession, 
        user_id: str, 
        month: date
    ) -> Optional[UserUsage]:
        """Get user usage record for specific month"""
        result = await session.execute(
            select(UserUsage).where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.month == month
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def increment_user_usage(
        session: AsyncSession,
        user_id: str,
        campaigns_count: int = 0,
        ai_credits_count: int = 0,
        api_calls_count: int = 0
    ) -> UserUsage:
        """Increment user usage for current month"""
        current_month = date.today().replace(day=1)
        
        # Get or create usage record
        usage = await DatabaseUtils.get_user_usage_for_month(session, user_id, current_month)
        if not usage:
            usage = UserUsage(
                user_id=user_id,
                month=current_month,
                campaigns_generated=0,
                ai_credits_used=0,
                api_calls_made=0
            )
            session.add(usage)
        
        # Increment counters
        usage.campaigns_generated += campaigns_count
        usage.ai_credits_used += ai_credits_count
        usage.api_calls_made += api_calls_count
        
        await session.commit()
        return usage
    
    @staticmethod
    async def track_ai_cost(
        session: AsyncSession,
        user_id: str,
        model_used: str,
        cost: Decimal,
        tokens_used: int = 0
    ):
        """Track AI usage cost for a user"""
        today = date.today()
        
        # Get or create cost tracking record
        result = await session.execute(
            select(AICostTracking).where(
                and_(
                    AICostTracking.user_id == user_id,
                    AICostTracking.date == today
                )
            )
        )
        cost_record = result.scalar_one_or_none()
        
        if not cost_record:
            cost_record = AICostTracking(
                user_id=user_id,
                date=today,
                openai_cost=Decimal('0'),
                anthropic_cost=Decimal('0'),
                total_cost=Decimal('0'),
                generations_count=0,
                tokens_used=0
            )
            session.add(cost_record)
        
        # Update costs based on model
        if 'gpt' in model_used.lower() or 'openai' in model_used.lower():
            cost_record.openai_cost += cost
        elif 'claude' in model_used.lower() or 'anthropic' in model_used.lower():
            cost_record.anthropic_cost += cost
        
        cost_record.total_cost += cost
        cost_record.generations_count += 1
        cost_record.tokens_used += tokens_used
        
        await session.commit()
        return cost_record
    
    @staticmethod
    async def check_user_limits(
        session: AsyncSession, 
        user_id: str, 
        subscription_tier: str
    ) -> Dict[str, Any]:
        """Check if user is within subscription limits"""
        from config import SUBSCRIPTION_LIMITS
        
        limits = SUBSCRIPTION_LIMITS.get(subscription_tier, SUBSCRIPTION_LIMITS['freemium'])
        current_month = date.today().replace(day=1)
        
        # Get current month usage
        usage = await DatabaseUtils.get_user_usage_for_month(session, user_id, current_month)
        if not usage:
            current_usage = {
                'campaigns_generated': 0,
                'ai_credits_used': 0,
                'storage_bytes_used': 0,
                'api_calls_made': 0
            }
        else:
            current_usage = {
                'campaigns_generated': usage.campaigns_generated,
                'ai_credits_used': usage.ai_credits_used,
                'storage_bytes_used': usage.storage_bytes_used,
                'api_calls_made': usage.api_calls_made
            }
        
        # Check limits
        within_limits = {
            'campaigns': current_usage['campaigns_generated'] < limits['campaigns_per_month'],
            'ai_credits': current_usage['ai_credits_used'] < limits['ai_credits'],
            'storage': current_usage['storage_bytes_used'] < (limits['storage_gb'] * 1024 * 1024 * 1024),
            'overall': True
        }
        
        within_limits['overall'] = all(within_limits.values())
        
        return {
            'within_limits': within_limits,
            'current_usage': current_usage,
            'limits': limits,
            'usage_percentages': {
                'campaigns': (current_usage['campaigns_generated'] / limits['campaigns_per_month']) * 100,
                'ai_credits': (current_usage['ai_credits_used'] / limits['ai_credits']) * 100,
                'storage': (current_usage['storage_bytes_used'] / (limits['storage_gb'] * 1024 * 1024 * 1024)) * 100
            }
        }
    
    @staticmethod
    async def get_user_campaigns(
        session: AsyncSession,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Campaign]:
        """Get user campaigns with optional filtering"""
        query = select(Campaign).where(Campaign.user_id == user_id)
        
        if status:
            query = query.where(Campaign.status == status)
        
        query = query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_campaign_analytics(
        session: AsyncSession,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a campaign"""
        # Get campaign with components
        result = await session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return {}
        
        # Get component analytics
        component_result = await session.execute(
            select(CampaignComponent).where(CampaignComponent.campaign_id == campaign_id)
        )
        components = component_result.scalars().all()
        
        # Calculate totals
        total_component_views = sum(c.views for c in components)
        total_component_clicks = sum(c.clicks for c in components)
        total_component_conversions = sum(c.conversions for c in components)
        
        return {
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'status': campaign.status,
                'views': campaign.views,
                'conversions': campaign.conversions,
                'revenue_generated': float(campaign.revenue_generated),
                'conversion_rate': (campaign.conversions / campaign.views * 100) if campaign.views > 0 else 0
            },
            'components': [
                {
                    'id': c.id,
                    'name': c.name,
                    'type': c.component_type,
                    'views': c.views,
                    'clicks': c.clicks,
                    'conversions': c.conversions,
                    'engagement_score': float(c.engagement_score),
                    'click_through_rate': (c.clicks / c.views * 100) if c.views > 0 else 0,
                    'conversion_rate': (c.conversions / c.clicks * 100) if c.clicks > 0 else 0
                }
                for c in components
            ],
            'totals': {
                'component_views': total_component_views,
                'component_clicks': total_component_clicks,
                'component_conversions': total_component_conversions,
                'overall_ctr': (total_component_clicks / total_component_views * 100) if total_component_views > 0 else 0
            }
        }
    
    @staticmethod
    async def search_campaigns(
        session: AsyncSession,
        user_id: str,
        search_query: str,
        limit: int = 20
    ) -> List[Campaign]:
        """Search campaigns using full-text search"""
        # For now, use simple ILIKE search. In production, use PostgreSQL full-text search
        query = select(Campaign).where(
            and_(
                Campaign.user_id == user_id,
                or_(
                    Campaign.name.ilike(f'%{search_query}%'),
                    Campaign.description.ilike(f'%{search_query}%'),
                    Campaign.target_audience.ilike(f'%{search_query}%')
                )
            )
        ).order_by(Campaign.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_ai_generation_stats(
        session: AsyncSession,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get AI generation statistics for a user"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await session.execute(
            select(
                func.count(AIGeneration.id).label('total_generations'),
                func.avg(AIGeneration.cost).label('avg_cost'),
                func.sum(AIGeneration.cost).label('total_cost'),
                func.avg(AIGeneration.generation_time_seconds).label('avg_time'),
                func.avg(AIGeneration.user_rating).label('avg_rating')
            ).where(
                and_(
                    AIGeneration.user_id == user_id,
                    AIGeneration.created_at >= start_date,
                    AIGeneration.status == 'completed'
                )
            )
        )
        
        stats = result.first()
        
        # Get generation breakdown by type
        type_result = await session.execute(
            select(
                AIGeneration.generation_type,
                func.count(AIGeneration.id).label('count')
            ).where(
                and_(
                    AIGeneration.user_id == user_id,
                    AIGeneration.created_at >= start_date,
                    AIGeneration.status == 'completed'
                )
            ).group_by(AIGeneration.generation_type)
        )
        
        generation_types = {row.generation_type: row.count for row in type_result}
        
        return {
            'total_generations': stats.total_generations or 0,
            'average_cost': float(stats.avg_cost or 0),
            'total_cost': float(stats.total_cost or 0),
            'average_time_seconds': float(stats.avg_time or 0),
            'average_rating': float(stats.avg_rating or 0),
            'generation_types': generation_types,
            'period_days': days
        }