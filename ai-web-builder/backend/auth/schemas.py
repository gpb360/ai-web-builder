"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any
from datetime import datetime

class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    subscription_tier: Optional[str] = "freemium"
    
    @validator('password')
    def validate_password(cls, v):
        from auth.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Password validation failed: {', '.join(validation['issues'])}")
        return v
    
    @validator('subscription_tier')
    def validate_subscription_tier(cls, v):
        if v not in ['freemium', 'creator', 'business', 'agency']:
            raise ValueError('Invalid subscription tier')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        from auth.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Password validation failed: {', '.join(validation['issues'])}")
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        from auth.security import validate_password_strength
        validation = validate_password_strength(v)
        if not validation["is_valid"]:
            raise ValueError(f"Password validation failed: {', '.join(validation['issues'])}")
        return v

class EmailVerification(BaseModel):
    token: str

class TokenRefresh(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    subscription_tier: str
    subscription_status: str
    subscription_ends_at: Optional[datetime] = None
    created_at: datetime
    last_active_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PasswordStrengthResponse(BaseModel):
    is_valid: bool
    strength: str
    issues: list[str]

class AuthStatus(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    session_info: Optional[Dict[str, Any]] = None

class RateLimitInfo(BaseModel):
    limit: int
    remaining: int
    reset_time: datetime
    
class SecurityEvent(BaseModel):
    event_type: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None