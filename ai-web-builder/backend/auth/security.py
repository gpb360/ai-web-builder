"""
Security utilities for authentication and password handling
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from config import settings
import secrets
import hashlib

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storage"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
            
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            return None
            
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None
            
        return payload
    except JWTError:
        return None

def generate_reset_token() -> str:
    """Generate secure password reset token"""
    return secrets.token_urlsafe(32)

def generate_verification_token() -> str:
    """Generate email verification token"""
    return secrets.token_urlsafe(32)

def create_session_id() -> str:
    """Create unique session identifier"""
    return secrets.token_urlsafe(16)

def hash_token(token: str) -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

class TokenManager:
    """Manage tokens with Redis storage for revocation"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def revoke_token(self, token: str) -> bool:
        """Add token to blacklist"""
        try:
            payload = verify_token(token)
            if not payload:
                return False
                
            # Get token expiry
            exp = payload.get("exp")
            if exp:
                # Store in blacklist until expiry
                ttl = exp - datetime.now(timezone.utc).timestamp()
                if ttl > 0:
                    await self.redis.setex(f"blacklist:{token}", int(ttl), "1")
            
            return True
        except Exception:
            return False
    
    async def is_token_revoked(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            return await self.redis.exists(f"blacklist:{token}")
        except Exception:
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revoke all tokens for a user"""
        try:
            # Store user in global revocation list with timestamp
            current_time = datetime.now(timezone.utc).timestamp()
            await self.redis.set(f"user_revoke:{user_id}", current_time)
            return True
        except Exception:
            return False
    
    async def is_user_tokens_revoked(self, user_id: str, token_issued_at: float) -> bool:
        """Check if user tokens issued before a certain time are revoked"""
        try:
            revoke_time = await self.redis.get(f"user_revoke:{user_id}")
            if revoke_time:
                return float(revoke_time) > token_issued_at
            return False
        except Exception:
            return False

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password meets security requirements"""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    
    # Check for common patterns
    common_passwords = [
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "dragon", "master"
    ]
    
    if password.lower() in common_passwords:
        issues.append("Password is too common")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "strength": calculate_password_strength(password)
    }

def calculate_password_strength(password: str) -> str:
    """Calculate password strength score"""
    score = 0
    
    # Length bonus
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    # Character variety
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    
    # Complexity patterns
    if len(set(password)) > len(password) * 0.6:  # Character diversity
        score += 1
    
    if score <= 3:
        return "weak"
    elif score <= 5:
        return "medium"
    elif score <= 7:
        return "strong"
    else:
        return "very_strong"