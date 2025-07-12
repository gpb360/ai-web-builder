from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db, get_redis
from auth.service import AuthService
from auth.schemas import (
    UserRegistration, UserLogin, TokenResponse, RefreshTokenResponse,
    PasswordReset, PasswordResetConfirm, PasswordChange, UserResponse,
    TokenRefresh, UserProfile, PasswordStrengthResponse, AuthStatus
)
from auth.dependencies import (
    get_current_user, get_optional_current_user, check_login_rate_limit,
    check_registration_rate_limit, check_password_reset_rate_limit,
    get_client_info
)
from auth.security import validate_password_strength, verify_token
from database.models import User
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register_user(
    registration_data: UserRegistration,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    _: None = Depends(check_registration_rate_limit)
):
    """Register a new user account"""
    try:
        client_info = get_client_info(request)
        auth_service = AuthService(db, redis_client)
        
        user, token_response = await auth_service.register_user(registration_data, client_info)
        
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    _: None = Depends(check_login_rate_limit)
):
    """Authenticate user and return tokens"""
    try:
        client_info = get_client_info(request)
        auth_service = AuthService(db, redis_client)
        
        token_response = await auth_service.authenticate_user(login_data, client_info)
        
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Refresh access token using refresh token"""
    try:
        auth_service = AuthService(db, redis_client)
        
        new_token = await auth_service.refresh_access_token(token_data.refresh_token)
        
        return new_token
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Logout user by revoking current session tokens"""
    try:
        # Extract tokens from request
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization header"
            )
        
        access_token = auth_header.split(" ")[1]
        
        # Get refresh token from request body if provided
        body = await request.json() if request.method == "POST" else {}
        refresh_token = body.get("refresh_token", "")
        
        auth_service = AuthService(db, redis_client)
        await auth_service.logout_user(access_token, refresh_token)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Logout user from all sessions"""
    try:
        auth_service = AuthService(db, redis_client)
        await auth_service.logout_all_sessions(str(current_user.id))
        
        return {"message": "Successfully logged out from all sessions"}
        
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout all failed"
        )

@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    _: None = Depends(check_password_reset_rate_limit)
):
    """Request password reset email"""
    try:
        client_info = get_client_info(request)
        auth_service = AuthService(db, redis_client)
        
        await auth_service.initiate_password_reset(reset_data, client_info)
        
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Confirm password reset with token"""
    try:
        client_info = get_client_info(request)
        auth_service = AuthService(db, redis_client)
        
        success = await auth_service.confirm_password_reset(reset_confirm, client_info)
        
        if success:
            return {"message": "Password has been reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset confirm error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.post("/password/change")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Change user password"""
    try:
        auth_service = AuthService(db, redis_client)
        
        success = await auth_service.change_password(current_user, password_change)
        
        if success:
            return {"message": "Password changed successfully. Please log in again."}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Update user profile"""
    try:
        auth_service = AuthService(db, redis_client)
        
        updated_user = await auth_service.update_user_profile(
            current_user, 
            profile_data.model_dump(exclude_unset=True)
        )
        
        return UserResponse.model_validate(updated_user)
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get authentication status"""
    try:
        if not current_user:
            return AuthStatus(authenticated=False)
        
        auth_service = AuthService(db, redis_client)
        session_info = await auth_service.validate_user_session(current_user)
        
        return AuthStatus(
            authenticated=True,
            user=UserResponse.model_validate(current_user),
            session_info=session_info
        )
        
    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return AuthStatus(authenticated=False)

@router.post("/validate-password", response_model=PasswordStrengthResponse)
async def validate_password(
    password_data: dict
):
    """Validate password strength"""
    password = password_data.get("password", "")
    
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    validation_result = validate_password_strength(password)
    
    return PasswordStrengthResponse(
        is_valid=validation_result["is_valid"],
        strength=validation_result["strength"],
        issues=validation_result["issues"]
    )

@router.post("/verify-token")
async def verify_access_token(
    token_data: dict
):
    """Verify if a token is valid"""
    token = token_data.get("token", "")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    payload = verify_token(token, "access")
    
    if payload:
        return {
            "valid": True,
            "expires_at": payload.get("exp"),
            "user_id": payload.get("sub"),
            "email": payload.get("email")
        }
    else:
        return {"valid": False}