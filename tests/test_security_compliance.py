import pytest
from fastapi.testclient import TestClient
from fastapi import status
import jwt
import ssl
import socket
from datetime import datetime, timedelta
import re
import requests
from typing import List, Dict

from main import app
from models.users import UserCreate

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def security_headers_required():
    """List of required security headers."""
    return [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "Referrer-Policy"
    ]

@pytest.fixture
def content_security_policy_directives():
    """Required CSP directives."""
    return [
        "default-src",
        "script-src",
        "style-src",
        "img-src",
        "connect-src",
        "font-src",
        "object-src",
        "media-src",
        "frame-src"
    ]

@pytest.mark.asyncio
async def test_security_headers(
    test_client: TestClient,
    security_headers_required: List[str],
    content_security_policy_directives: List[str]
):
    """Test security headers compliance."""
    response = test_client.get("/")
    headers = response.headers
    
    # Check required security headers
    for header in security_headers_required:
        assert header in headers, f"Missing security header: {header}"
    
    # Validate Content-Security-Policy
    csp = headers.get("Content-Security-Policy", "")
    for directive in content_security_policy_directives:
        assert directive in csp, f"Missing CSP directive: {directive}"
    
    # Validate specific header values
    assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "max-age" in headers["Strict-Transport-Security"]
    assert headers["Referrer-Policy"] in [
        "no-referrer",
        "strict-origin",
        "strict-origin-when-cross-origin"
    ]

@pytest.mark.asyncio
async def test_cookie_security(test_client: TestClient):
    """Test cookie security settings."""
    response = test_client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123!"
        }
    )
    
    for cookie in response.cookies:
        # Check secure flag
        assert cookie.secure, f"Cookie {cookie.name} must be secure"
        
        # Check HttpOnly flag
        assert cookie.has_nonstandard_attr("HttpOnly"), \
            f"Cookie {cookie.name} must be HttpOnly"
        
        # Check SameSite attribute
        assert cookie.has_nonstandard_attr("SameSite"), \
            f"Cookie {cookie.name} must have SameSite attribute"
        
        # Check appropriate expiration
        if cookie.name != "csrf_token":  # Exclude session cookies
            assert cookie.expires, f"Cookie {cookie.name} must have expiration"
            expiration = datetime.fromtimestamp(cookie.expires)
            assert expiration > datetime.now(), \
                f"Cookie {cookie.name} must not be expired"
            assert expiration < datetime.now() + timedelta(days=90), \
                f"Cookie {cookie.name} expiration too far in future"

@pytest.mark.asyncio
async def test_password_policy_compliance(
    test_client: TestClient
):
    """Test password policy compliance."""
    test_cases = [
        {
            "password": "short",
            "should_pass": False,
            "reason": "too short"
        },
        {
            "password": "nocapitals123!",
            "should_pass": False,
            "reason": "no capitals"
        },
        {
            "password": "NoSpecialChar123",
            "should_pass": False,
            "reason": "no special chars"
        },
        {
            "password": "NoNumbers!",
            "should_pass": False,
            "reason": "no numbers"
        },
        {
            "password": "ValidPass123!",
            "should_pass": True,
            "reason": "meets all requirements"
        }
    ]
    
    for test_case in test_cases:
        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": test_case["password"],
                "full_name": "Test User"
            }
        )
        
        if test_case["should_pass"]:
            assert response.status_code == status.HTTP_201_CREATED, \
                f"Valid password rejected: {test_case['password']}"
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST, \
                f"Invalid password accepted: {test_case['password']}, {test_case['reason']}"

@pytest.mark.asyncio
async def test_session_security(
    test_client: TestClient,
    auth_token: str
):
    """Test session security compliance."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Test session timeout
    time.sleep(1800)  # 30 minutes
    response = test_client.get("/documents", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        "Session should timeout after inactivity"
    
    # 2. Test concurrent session handling
    # Login from "another device"
    response = test_client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123!"
        }
    )
    new_token = response.json()["access_token"]
    
    # Original session should be invalidated
    response = test_client.get(
        "/documents",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        "Original session should be invalidated"
    
    # New session should work
    response = test_client.get(
        "/documents",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert response.status_code == status.HTTP_200_OK, \
        "New session should be valid"

@pytest.mark.asyncio
async def test_api_rate_limiting_compliance(
    test_client: TestClient,
    auth_token: str
):
    """Test API rate limiting compliance."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    endpoints = [
        ("/documents", "GET"),
        ("/documents/search", "POST"),
        ("/templates", "GET"),
        ("/users/profile", "GET")
    ]
    
    for endpoint, method in endpoints:
        # Test rate limiting
        for _ in range(100):  # Attempt to trigger rate limit
            response = test_client.request(method, endpoint, headers=headers)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        else:
            assert False, f"Rate limiting not enforced for {method} {endpoint}"
        
        # Verify rate limit headers
        assert "X-RateLimit-Limit" in response.headers, \
            f"Missing rate limit headers for {method} {endpoint}"
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify retry-after header
        assert "Retry-After" in response.headers, \
            f"Missing Retry-After header for {method} {endpoint}"
        
        # Test rate limit reset
        retry_after = int(response.headers["Retry-After"])
        time.sleep(retry_after)
        response = test_client.request(method, endpoint, headers=headers)
        assert response.status_code == status.HTTP_200_OK, \
            f"Rate limit not reset after waiting for {method} {endpoint}" 