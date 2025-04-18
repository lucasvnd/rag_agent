import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Import your FastAPI app to create test client
# Adjust the import path based on your actual application structure
from main import app

@pytest.fixture
def test_client():
    """Return a FastAPI TestClient which uses the app."""
    return TestClient(app)

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = MagicMock()
    
    # Configure the mock to return predictable responses
    # Adjust these based on your actual Supabase methods used
    mock.table().select().execute.return_value = {"data": []}
    mock.storage().from_().upload.return_value = {"Key": "test-file.pdf"}
    
    return mock

@pytest.fixture
def sample_pdf():
    """Return sample PDF content for testing."""
    # This is a minimal PDF file for testing purposes
    return b"%PDF-1.3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000102 00000 n \ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"

@pytest.fixture
def sample_docx():
    """Return sample DOCX content for testing."""
    # This is not actual DOCX content, but a placeholder
    # In a real test, you might read this from a file in the fixtures directory
    return b"Sample DOCX content"

@pytest.fixture
def sample_txt():
    """Return sample text content for testing."""
    return b"This is a sample text document for testing.\nIt has multiple lines.\nEach line contains text that can be processed."

@pytest.fixture
def sample_embedding():
    """Return a sample vector embedding for testing."""
    # A small sample vector - actual embeddings would be larger
    import numpy as np
    return np.random.rand(1536).tolist()  # OpenAI embeddings are 1536 dimensions

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client for embeddings."""
    mock = MagicMock()
    
    # Configure the mock to return predictable responses
    mock.embeddings.create.return_value = {
        "data": [
            {
                "embedding": [0.1] * 1536,  # Simple repeated value for testing
                "index": 0,
                "object": "embedding"
            }
        ],
        "model": "text-embedding-ada-002",
        "object": "list",
        "usage": {
            "prompt_tokens": 8,
            "total_tokens": 8
        }
    }
    
    return mock 