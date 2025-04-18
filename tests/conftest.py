import os
import sys
import pytest
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.document_processor import DocumentProcessor

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def test_user():
    """Provide a test user for document processing."""
    return {
        "id": "test_user_id",
        "name": "Test User"
    }

@pytest.fixture
def db_session():
    """Mock database session for testing."""
    class MockSession:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
        async def commit(self):
            pass
        
        async def rollback(self):
            pass
    
    return MockSession()

@pytest.fixture
def document_processor(db_session, temp_dir):
    """Create a DocumentProcessor instance for testing."""
    return DocumentProcessor(db_session, temp_dir) 