import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID
import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from services.auth import AuthService, get_password_hash, verify_password
from models.users import User, UserCreate, UserInDB

# Test constants
TEST_SECRET_KEY = "test_secret_key"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30

@pytest.fixture
def auth_service(db_session):
    return AuthService(
        db_session,
        secret_key=TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
        access_token_expire_minutes=TEST_ACCESS_TOKEN_EXPIRE_MINUTES
    )

@pytest.fixture
def test_user_create():
    return UserCreate(
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )

@pytest.fixture
def test_user_in_db(test_user_create):
    hashed_password = get_password_hash(test_user_create.password)
    return UserInDB(
        id=UUID('12345678-1234-5678-1234-567812345678'),
        email=test_user_create.email,
        hashed_password=hashed_password,
        full_name=test_user_create.full_name,
        is_active=True
    )

@pytest.mark.asyncio
async def test_create_user(auth_service: AuthService, test_user_create: UserCreate):
    """Test user creation."""
    user = await auth_service.create_user(test_user_create)
    
    assert user.email == test_user_create.email
    assert user.full_name == test_user_create.full_name
    assert user.is_active
    assert hasattr(user, "id")
    assert not hasattr(user, "hashed_password")

@pytest.mark.asyncio
async def test_authenticate_user(auth_service: AuthService, test_user_create: UserCreate):
    """Test user authentication."""
    # Create user first
    await auth_service.create_user(test_user_create)
    
    # Test authentication
    user = await auth_service.authenticate_user(
        test_user_create.email,
        test_user_create.password
    )
    
    assert user is not None
    assert user.email == test_user_create.email
    assert not hasattr(user, "hashed_password")

@pytest.mark.asyncio
async def test_create_access_token(auth_service: AuthService, test_user_in_db: UserInDB):
    """Test access token creation."""
    access_token = await auth_service.create_access_token(
        data={"sub": test_user_in_db.email}
    )
    
    assert isinstance(access_token, str)
    
    # Verify token
    payload = jwt.decode(
        access_token,
        TEST_SECRET_KEY,
        algorithms=[TEST_ALGORITHM]
    )
    assert payload["sub"] == test_user_in_db.email
    assert "exp" in payload

@pytest.mark.asyncio
async def test_get_current_user(auth_service: AuthService, test_user_in_db: UserInDB):
    """Test getting current user from token."""
    # Create token
    access_token = await auth_service.create_access_token(
        data={"sub": test_user_in_db.email}
    )
    
    # Get current user
    current_user = await auth_service.get_current_user(access_token)
    
    assert current_user.email == test_user_in_db.email
    assert current_user.is_active

@pytest.mark.asyncio
async def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

@pytest.mark.asyncio
async def test_invalid_authentication(auth_service: AuthService, test_user_create: UserCreate):
    """Test authentication with invalid credentials."""
    # Create user first
    await auth_service.create_user(test_user_create)
    
    # Test with wrong password
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            test_user_create.email,
            "wrongpassword"
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test with non-existent user
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(
            "nonexistent@example.com",
            test_user_create.password
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_inactive_user(auth_service: AuthService, test_user_in_db: UserInDB):
    """Test authentication with inactive user."""
    # Set user as inactive
    test_user_in_db.is_active = False
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(
            await auth_service.create_access_token(
                data={"sub": test_user_in_db.email}
            )
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_token_expiration(auth_service: AuthService, test_user_in_db: UserInDB):
    """Test token expiration."""
    # Create token with short expiration
    access_token = await auth_service.create_access_token(
        data={"sub": test_user_in_db.email},
        expires_delta=timedelta(microseconds=1)
    )
    
    # Wait for token to expire
    await asyncio.sleep(0.1)
    
    # Try to get current user with expired token
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_current_user(access_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_duplicate_user(auth_service: AuthService, test_user_create: UserCreate):
    """Test creating duplicate user."""
    # Create user first time
    await auth_service.create_user(test_user_create)
    
    # Try to create same user again
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.create_user(test_user_create)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_password_validation(auth_service: AuthService):
    """Test password validation rules."""
    # Test with short password
    user_with_short_password = UserCreate(
        email="test@example.com",
        password="short",
        full_name="Test User"
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.create_user(user_with_short_password)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST 