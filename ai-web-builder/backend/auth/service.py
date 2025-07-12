"""
Authentication service with business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import User, UserUsage
from database.utils import DatabaseUtils
from auth.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, generate_reset_token,
    generate_verification_token, TokenManager
)
from auth.schemas import (
    UserRegistration, UserLogin, PasswordReset, PasswordResetConfirm,
    PasswordChange, UserResponse, TokenResponse, RefreshTokenResponse
)
from config import settings
from datetime import datetime, timedelta, timezone, date
from typing import Optional, Dict, Any, Tuple
import uuid
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service handling all auth operations"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.token_manager = TokenManager(redis_client) if redis_client else None
    
    async def register_user(
        self, 
        registration_data: UserRegistration,
        client_info: Dict[str, Any]
    ) -> Tuple[User, TokenResponse]:
        """Register a new user"""
        
        # Check if user already exists
        existing_user = await DatabaseUtils.get_user_by_email(self.db, registration_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        user = User(
            email=registration_data.email,
            password_hash=get_password_hash(registration_data.password),
            name=registration_data.name,
            subscription_tier=registration_data.subscription_tier,
            subscription_status='active',
            settings={
                "theme": "light",
                "notifications": {
                    "email_notifications": True,
                    "campaign_updates": True,
                    "billing_alerts": True,
                    "feature_announcements": True
                },
                "ai_preferences": {
                    "preferred_style": "modern",
                    "animation_level": "smooth",
                    "responsiveness_priority": "mobile",
                    "accessibility_mode": False
                }
            }
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Create initial usage record
        current_month = date.today().replace(day=1)
        usage = UserUsage(
            user_id=user.id,
            month=current_month,
            campaigns_generated=0,
            ai_credits_used=0,
            storage_bytes_used=0,
            api_calls_made=0
        )
        self.db.add(usage)
        await self.db.commit()
        
        # Generate tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Log registration event
        logger.info(f"User registered: {user.email} from IP: {client_info.get('ip_address')}")
        
        # Create response
        user_response = UserResponse.model_validate(user)
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
        
        return user, token_response
    
    async def authenticate_user(
        self,
        login_data: UserLogin,
        client_info: Dict[str, Any]
    ) -> Optional[TokenResponse]:
        """Authenticate user and return tokens"""
        
        # Get user by email
        user = await DatabaseUtils.get_user_by_email(self.db, login_data.email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Log failed login attempt
            logger.warning(f"Failed login attempt for {login_data.email} from IP: {client_info.get('ip_address')}")
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # Update last active time
        user.last_active_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # Generate tokens
        token_data = {"sub": str(user.id), "email": user.email}
        
        # Adjust token expiry if remember_me is True
        if login_data.remember_me:
            access_token_expires = timedelta(days=7)  # Extended session
        else:
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        
        access_token = create_access_token(token_data, access_token_expires)
        refresh_token = create_refresh_token(token_data)
        
        # Log successful login
        logger.info(f"User logged in: {user.email} from IP: {client_info.get('ip_address')}")
        
        # Create response
        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=user_response
        )
    
    async def refresh_access_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Generate new access token using refresh token"""
        
        # Verify refresh token
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid refresh token")
        
        # Check if token is revoked
        if self.token_manager and await self.token_manager.is_token_revoked(refresh_token):
            raise ValueError("Refresh token has been revoked")
        
        # Get user
        user = await DatabaseUtils.get_user_by_email(self.db, payload.get("email"))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Check if user tokens are globally revoked
        user_id = payload.get("sub")
        token_issued_at = payload.get("iat", 0)
        if self.token_manager and await self.token_manager.is_user_tokens_revoked(user_id, token_issued_at):
            raise ValueError("User session has been invalidated")
        
        # Generate new access token
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def logout_user(self, access_token: str, refresh_token: str) -> bool:
        """Logout user by revoking tokens"""
        
        if not self.token_manager:
            return True  # If no Redis, just consider it logged out
        
        # Revoke both tokens
        await self.token_manager.revoke_token(access_token)
        await self.token_manager.revoke_token(refresh_token)
        
        return True
    
    async def logout_all_sessions(self, user_id: str) -> bool:
        """Logout user from all sessions"""
        
        if not self.token_manager:
            return True
        
        # Revoke all user tokens
        await self.token_manager.revoke_all_user_tokens(user_id)
        
        return True
    
    async def change_password(
        self,
        user: User,
        password_change: PasswordChange
    ) -> bool:
        """Change user password"""
        
        # Verify current password
        if not verify_password(password_change.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.password_hash = get_password_hash(password_change.new_password)
        await self.db.commit()
        
        # Revoke all existing tokens for security
        if self.token_manager:
            await self.token_manager.revoke_all_user_tokens(str(user.id))
        
        logger.info(f"Password changed for user: {user.email}")
        return True
    
    async def initiate_password_reset(
        self,
        password_reset: PasswordReset,
        client_info: Dict[str, Any]
    ) -> str:
        """Initiate password reset process"""
        
        # Check if user exists
        user = await DatabaseUtils.get_user_by_email(self.db, password_reset.email)
        if not user:
            # Don't reveal if email exists, but log the attempt
            logger.warning(f"Password reset attempt for non-existent email: {password_reset.email}")
            return "reset_token"  # Return dummy token
        
        # Generate reset token
        reset_token = generate_reset_token()
        
        # Store reset token in Redis with expiry
        if self.redis:
            await self.redis.setex(
                f"password_reset:{reset_token}",
                3600,  # 1 hour expiry
                str(user.id)
            )
        
        # TODO: Send email with reset link
        # For now, just log it
        logger.info(f"Password reset requested for: {user.email}, token: {reset_token}")
        
        return reset_token
    
    async def confirm_password_reset(
        self,
        reset_confirm: PasswordResetConfirm,
        client_info: Dict[str, Any]
    ) -> bool:
        """Confirm password reset with token"""
        
        if not self.redis:
            raise ValueError("Password reset not available")
        
        # Get user ID from token
        user_id = await self.redis.get(f"password_reset:{reset_confirm.token}")
        if not user_id:
            raise ValueError("Invalid or expired reset token")
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        
        # Update password
        user.password_hash = get_password_hash(reset_confirm.new_password)
        await self.db.commit()
        
        # Delete reset token
        await self.redis.delete(f"password_reset:{reset_confirm.token}")
        
        # Revoke all existing tokens
        if self.token_manager:
            await self.token_manager.revoke_all_user_tokens(str(user.id))
        
        logger.info(f"Password reset completed for user: {user.email}")
        return True
    
    async def update_user_profile(
        self,
        user: User,
        profile_data: Dict[str, Any]
    ) -> User:
        """Update user profile information"""
        
        # Update allowed fields
        if 'name' in profile_data and profile_data['name']:
            user.name = profile_data['name']
        
        if 'avatar_url' in profile_data:
            user.avatar_url = profile_data['avatar_url']
        
        if 'settings' in profile_data and profile_data['settings']:
            # Merge settings instead of replacing
            current_settings = user.settings or {}
            current_settings.update(profile_data['settings'])
            user.settings = current_settings
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Profile updated for user: {user.email}")
        return user
    
    async def get_user_security_events(
        self,
        user: User,
        limit: int = 50
    ) -> list:
        """Get user security events (placeholder for future implementation)"""
        
        # TODO: Implement security event logging and retrieval
        # This would track login attempts, password changes, etc.
        return []
    
    async def validate_user_session(self, user: User) -> Dict[str, Any]:
        """Validate and return user session information"""
        
        # Check subscription status
        subscription_valid = True
        if user.subscription_ends_at and user.subscription_ends_at < datetime.now(timezone.utc):
            subscription_valid = False
        
        # Get current usage
        usage_info = await DatabaseUtils.check_user_limits(
            self.db, 
            str(user.id), 
            user.subscription_tier
        )
        
        return {
            "user_id": str(user.id),
            "subscription_valid": subscription_valid,
            "subscription_tier": user.subscription_tier,
            "usage_info": usage_info,
            "account_status": "active" if user.is_active else "disabled"
        }