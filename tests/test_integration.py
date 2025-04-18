import pytest
from pathlib import Path
import asyncio
from typing import Dict, Any
from uuid import UUID
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI, status

from main import app
from services.auth import AuthService
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore
from models.users import UserCreate
from models.documents import Document

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def auth_token(test_client: TestClient, test_user_create: UserCreate):
    """Create a test user and get authentication token."""
    # Register user
    response = test_client.post(
        "/auth/register",
        json={
            "email": test_user_create.email,
            "password": test_user_create.password,
            "full_name": test_user_create.full_name
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Login to get token
    response = test_client.post(
        "/auth/login",
        data={
            "username": test_user_create.email,
            "password": test_user_create.password
        }
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_complete_document_workflow(
    test_client: TestClient,
    auth_token: str,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test complete document processing workflow from upload to search."""
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
    assert response.status_code == status.HTTP_201_CREATED
    document_id = response.json()["id"]
    
    # 2. Wait for processing to complete
    max_retries = 10
    for _ in range(max_retries):
        response = test_client.get(f"/documents/{document_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        if response.json()["status"] == "completed":
            break
        await asyncio.sleep(1)
    assert response.json()["status"] == "completed"
    
    # 3. Search in document
    response = test_client.post(
        "/search",
        json={
            "query": "Test Content",
            "limit": 5
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) > 0
    assert "content" in results[0]
    assert "score" in results[0]

@pytest.mark.asyncio
async def test_template_workflow(
    test_client: TestClient,
    auth_token: str,
    temp_dir: Path
):
    """Test complete template management workflow."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Create template
    template_data = {
        "name": "Test Template",
        "description": "Test template description",
        "content": "Template with {{variable1}} and {{variable2}}"
    }
    response = test_client.post(
        "/templates",
        json=template_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    template_id = response.json()["id"]
    
    # 2. Get template
    response = test_client.get(f"/templates/{template_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == template_data["name"]
    
    # 3. Update template
    update_data = {
        "name": "Updated Template",
        "description": "Updated description"
    }
    response = test_client.patch(
        f"/templates/{template_id}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == update_data["name"]
    
    # 4. Generate from template
    variables = {
        "variable1": "Value 1",
        "variable2": "Value 2"
    }
    response = test_client.post(
        f"/templates/{template_id}/generate",
        json={"variables": variables},
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert "Value 1" in response.json()["content"]
    assert "Value 2" in response.json()["content"]

@pytest.mark.asyncio
async def test_user_isolation_workflow(
    test_client: TestClient,
    auth_token: str,
    test_user_create: UserCreate,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test user data isolation in various operations."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Create another user
    other_user = UserCreate(
        email="other@example.com",
        password="testpassword123",
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
    assert response.status_code == status.HTTP_201_CREATED
    
    # Get token for other user
    response = test_client.post(
        "/auth/login",
        data={
            "username": other_user.email,
            "password": other_user.password
        }
    )
    assert response.status_code == status.HTTP_200_OK
    other_token = response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # 2. Upload document as first user
    test_file = temp_dir / "test.pdf"
    test_file.write_bytes(sample_pdf_content)
    
    with open(test_file, "rb") as f:
        response = test_client.post(
            "/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=headers
        )
    assert response.status_code == status.HTTP_201_CREATED
    document_id = response.json()["id"]
    
    # 3. Try to access first user's document as second user
    response = test_client.get(
        f"/documents/{document_id}",
        headers=other_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # 4. Create template as first user
    template_data = {
        "name": "Test Template",
        "description": "Test template description",
        "content": "Template content"
    }
    response = test_client.post(
        "/templates",
        json=template_data,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    template_id = response.json()["id"]
    
    # 5. Try to access first user's template as second user
    response = test_client.get(
        f"/templates/{template_id}",
        headers=other_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_error_handling_workflow(
    test_client: TestClient,
    auth_token: str,
    temp_dir: Path
):
    """Test error handling in various scenarios."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Try to upload invalid file
    invalid_file = temp_dir / "test.txt"
    invalid_file.write_text("Not a PDF")
    
    with open(invalid_file, "rb") as f:
        response = test_client.post(
            "/documents/upload",
            files={"file": ("test.txt", f, "text/plain")},
            headers=headers
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # 2. Try to access non-existent document
    response = test_client.get(
        f"/documents/{UUID('12345678-1234-5678-1234-567812345678')}",
        headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # 3. Try to search with invalid query
    response = test_client.post(
        "/search",
        json={
            "query": "",  # Empty query
            "limit": 5
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # 4. Try to create template with missing required fields
    response = test_client.post(
        "/templates",
        json={
            "name": "Test Template"
            # Missing description and content
        },
        headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_concurrent_operations(
    test_client: TestClient,
    auth_token: str,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test handling of concurrent operations."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create multiple test files
    test_files = []
    for i in range(5):
        test_file = temp_dir / f"test_{i}.pdf"
        test_file.write_bytes(sample_pdf_content)
        test_files.append(test_file)
    
    # Upload files concurrently
    async def upload_file(file_path):
        with open(file_path, "rb") as f:
            response = test_client.post(
                "/documents/upload",
                files={"file": (file_path.name, f, "application/pdf")},
                headers=headers
            )
        return response
    
    upload_tasks = [upload_file(f) for f in test_files]
    responses = await asyncio.gather(*upload_tasks)
    
    # Verify all uploads were successful
    for response in responses:
        assert response.status_code == status.HTTP_201_CREATED
    
    # Wait for all documents to be processed
    document_ids = [r.json()["id"] for r in responses]
    
    async def wait_for_processing(doc_id):
        max_retries = 10
        for _ in range(max_retries):
            response = test_client.get(f"/documents/{doc_id}", headers=headers)
            if response.json()["status"] == "completed":
                return response
            await asyncio.sleep(1)
        return response
    
    processing_tasks = [wait_for_processing(doc_id) for doc_id in document_ids]
    processing_results = await asyncio.gather(*processing_tasks)
    
    # Verify all documents were processed successfully
    for result in processing_results:
        assert result.json()["status"] == "completed" 