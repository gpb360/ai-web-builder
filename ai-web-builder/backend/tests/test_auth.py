"""
Tests for authentication system
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from auth.security import create_access_token, verify_password, hash_password

client = TestClient(app)

@pytest.mark.asyncio
async def test_user_registration():
    """Test user registration endpoint"""
    user_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # This would need proper test database setup
    # response = client.post("/api/auth/register", json=user_data)
    # assert response.status_code == 201
    pass

def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_jwt_token_creation():
    """Test JWT token creation"""
    user_data = {"sub": "test@example.com", "user_id": "123"}
    token = create_access_token(user_data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are typically long