"""
Authentication dependencies for FastAPI routes
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db, get_redis
from database.models import User
from database.utils import DatabaseUtils
from auth.security import verify_token, TokenManager
from typing import Optional
import time

security = HTTPBearer(auto_error=False)

class RateLimiter:
    """Rate limiting for authentication endpoints"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_seconds = window_minutes * 60
    
    async def check_rate_limit(self, key: str, redis_client) -> bool:
        """Check if request is within rate limit"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # Clean old attempts
            await redis_client.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
            
            # Count current attempts
            current_attempts = await redis_client.zcard(f"rate_limit:{key}")
            
            if current_attempts >= self.max_attempts:
                return False
            
            # Add current attempt
            await redis_client.zadd(f"rate_limit:{key}", {str(current_time): current_time})
            await redis_client.expire(f"rate_limit:{key}", self.window_seconds)
            
            return True
        except Exception:
            # If Redis fails, allow the request
            return True

# Rate limiters for different endpoints
login_rate_limiter = RateLimiter(max_attempts=5, window_minutes=15)
registration_rate_limiter = RateLimiter(max_attempts=3, window_minutes=60)
password_reset_rate_limiter = RateLimiter(max_attempts=3, window_minutes=60)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token is revoked
    token_manager = TokenManager(redis_client)
    if await token_manager.is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user tokens are globally revoked
    user_id = payload.get("sub")
    token_issued_at = payload.get("iat", 0)
    if await token_manager.is_user_tokens_revoked(user_id, token_issued_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await DatabaseUtils.get_user_by_email(db, payload.get("email"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for clarity)"""
    return current_user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        return await get_current_user(credentials, db, redis_client)
    except HTTPException:
        return None

def require_subscription_tier(required_tier: str):
    """Dependency factory for subscription tier requirements"""
    tier_hierarchy = {
        'freemium': 0,
        'creator': 1,
        'business': 2,
        'agency': 3
    }
    
    async def check_subscription_tier(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 999)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Subscription tier '{required_tier}' or higher required"
            )
        
        return current_user
    
    return check_subscription_tier

async def check_login_rate_limit(request: Request, redis_client = Depends(get_redis)):
    """Check rate limit for login attempts"""
    client_ip = request.client.host
    key = f"login:{client_ip}"
    
    if not await login_rate_limiter.check_rate_limit(key, redis_client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

async def check_registration_rate_limit(request: Request, redis_client = Depends(get_redis)):
    """Check rate limit for registration attempts"""
    client_ip = request.client.host
    key = f"registration:{client_ip}"
    
    if not await registration_rate_limiter.check_rate_limit(key, redis_client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )

async def check_password_reset_rate_limit(request: Request, redis_client = Depends(get_redis)):
    """Check rate limit for password reset attempts"""
    client_ip = request.client.host
    key = f"password_reset:{client_ip}"
    
    if not await password_reset_rate_limiter.check_rate_limit(key, redis_client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset attempts. Please try again later."
        )

def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "origin": request.headers.get("origin", ""),
        "referer": request.headers.get("referer", "")
    }