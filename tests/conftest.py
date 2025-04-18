import pytest
import os
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from databases import Database
import uuid
import shutil
from datetime import datetime

# Test database URL - using SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test vector store configuration
TEST_VECTOR_STORE = {
    "url": "postgresql://test:test@localhost:5432/test_vectors",
    "dimension": 1536
}

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def test_db(test_db_engine):
    """Create test database and tables."""
    async with test_db_engine.begin() as conn:
        # Create tables
        from database.models import Base
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_db_engine
    
    # Drop tables after tests
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db) -> AsyncSession:
    """Create a new database session for a test."""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "is_active": True
    }

@pytest.fixture
def test_document(test_user, temp_dir):
    """Create a test document."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_user["id"],
        "filename": "test_doc.pdf",
        "file_path": str(temp_dir / "test_doc.pdf"),
        "status": "pending",
        "metadata": {}
    }

@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing."""
    return [0.1] * 1536  # OpenAI's embedding dimension

@pytest.fixture
def mock_chunks(test_document):
    """Create mock document chunks for testing."""
    return [
        {
            "id": uuid.uuid4(),
            "document_id": test_document["id"],
            "user_id": test_document["user_id"],
            "content": f"Test content {i}",
            "embedding": [0.1] * 1536,
            "metadata": {"chunk_index": i}
        }
        for i in range(5)
    ]

@pytest.fixture
def test_template_dir(tmp_path) -> str:
    """Create a temporary directory for template files"""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    yield str(template_dir)
    shutil.rmtree(str(template_dir))

@pytest.fixture
def sample_template_data() -> Dict:
    """Sample template data for tests"""
    return {
        "id": "test-123",
        "name": "Test Template",
        "description": "A test template for unit tests",
        "file_path": "/templates/test.docx",
        "variables": {
            "name": "string",
            "age": "integer",
            "email": "string"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

@pytest.fixture
def sample_docx_template(test_template_dir) -> str:
    """Create a sample DOCX template file"""
    from docxtpl import DocxTemplate
    
    template_path = os.path.join(test_template_dir, "test_template.docx")
    doc = DocxTemplate(os.path.join(os.path.dirname(__file__), "data", "base_template.docx"))
    doc.save(template_path)
    return template_path

@pytest.fixture
def mock_db():
    """Mock database for testing"""
    class MockDB:
        def __init__(self):
            self.templates = {}
            self.documents = {}
            
        async def add_template(self, template):
            self.templates[template.id] = template
            
        async def get_template(self, template_id):
            return self.templates.get(template_id)
            
        async def list_templates(self):
            return list(self.templates.values())
            
        async def delete_template(self, template_id):
            if template_id in self.templates:
                del self.templates[template_id]
                
    return MockDB()

@pytest.fixture
def mock_file_storage(test_template_dir):
    """Mock file storage for testing"""
    class MockStorage:
        def __init__(self, base_dir):
            self.base_dir = base_dir
            
        def save_file(self, file_data, filename):
            path = os.path.join(self.base_dir, filename)
            with open(path, 'wb') as f:
                f.write(file_data)
            return path
            
        def delete_file(self, filename):
            path = os.path.join(self.base_dir, filename)
            if os.path.exists(path):
                os.remove(path)
                
    return MockStorage(test_template_dir)

@pytest.fixture
def test_client():
    """Create a test client for API testing"""
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app) 