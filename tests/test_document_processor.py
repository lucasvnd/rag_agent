import pytest
from pathlib import Path
import uuid
from datetime import datetime
from typing import Dict, Any, List
import json

from services.document_processor import DocumentProcessor
from models.documents import Document, DocumentCreate, DocumentStatus

@pytest.fixture
def document_processor(db_session, temp_dir):
    return DocumentProcessor(db_session, temp_dir)

@pytest.fixture
def sample_pdf_content():
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Test Content) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000254 00000 n\n0000000332 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n427\n%%EOF"

@pytest.mark.asyncio
async def test_document_creation(document_processor: DocumentProcessor, test_user: Dict, temp_dir: Path, sample_pdf_content: bytes):
    """Test creating a new document."""
    # Create a test PDF file
    test_file = temp_dir / "test.pdf"
    test_file.write_bytes(sample_pdf_content)
    
    doc = await document_processor.create_document(
        user_id=test_user["id"],
        filename="test.pdf",
        file_path=str(test_file)
    )
    
    assert isinstance(doc, Document)
    assert doc.user_id == test_user["id"]
    assert doc.filename == "test.pdf"
    assert doc.status == DocumentStatus.PENDING

@pytest.mark.asyncio
async def test_document_processing(document_processor: DocumentProcessor, test_document: Dict, temp_dir: Path, sample_pdf_content: bytes):
    """Test processing a document."""
    # Create a test PDF file
    test_file = Path(test_document["file_path"])
    test_file.write_bytes(sample_pdf_content)
    
    # Create document
    doc = Document(**test_document)
    
    # Process document
    processed_doc = await document_processor.process_document(doc)
    
    assert processed_doc.status == DocumentStatus.COMPLETED
    assert processed_doc.metadata.get("page_count") > 0
    assert processed_doc.metadata.get("chunk_count") > 0

@pytest.mark.asyncio
async def test_chunk_generation(document_processor: DocumentProcessor, test_document: Dict, temp_dir: Path, sample_pdf_content: bytes):
    """Test generating chunks from a document."""
    # Create a test PDF file
    test_file = Path(test_document["file_path"])
    test_file.write_bytes(sample_pdf_content)
    
    # Create document
    doc = Document(**test_document)
    
    # Generate chunks
    chunks = await document_processor.generate_chunks(doc)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.document_id == doc.id
        assert chunk.user_id == doc.user_id
        assert isinstance(chunk.content, str)
        assert len(chunk.content) > 0
        assert isinstance(chunk.metadata, dict)

@pytest.mark.asyncio
async def test_embedding_generation(document_processor: DocumentProcessor, test_document: Dict, mock_chunks: List[Dict]):
    """Test generating embeddings for chunks."""
    # Create document
    doc = Document(**test_document)
    
    # Generate embeddings for chunks
    chunks_with_embeddings = await document_processor.generate_embeddings(mock_chunks)
    
    assert len(chunks_with_embeddings) == len(mock_chunks)
    for chunk in chunks_with_embeddings:
        assert len(chunk["embedding"]) == 1536  # OpenAI's embedding dimension
        assert isinstance(chunk["embedding"], list)
        assert all(isinstance(x, float) for x in chunk["embedding"])

@pytest.mark.asyncio
async def test_error_handling(document_processor: DocumentProcessor, test_document: Dict, temp_dir: Path):
    """Test error handling during document processing."""
    # Create document with non-existent file
    doc = Document(**test_document)
    
    # Process document should handle the error
    processed_doc = await document_processor.process_document(doc)
    
    assert processed_doc.status == DocumentStatus.ERROR
    assert processed_doc.error_message is not None

@pytest.mark.asyncio
async def test_document_cleanup(document_processor: DocumentProcessor, test_document: Dict, temp_dir: Path, sample_pdf_content: bytes):
    """Test cleanup of temporary files after processing."""
    # Create a test PDF file
    test_file = Path(test_document["file_path"])
    test_file.write_bytes(sample_pdf_content)
    
    # Create document
    doc = Document(**test_document)
    
    # Process document
    processed_doc = await document_processor.process_document(doc)
    
    # Check that temporary files are cleaned up
    temp_files = list(temp_dir.glob("*.tmp"))
    assert len(temp_files) == 0

@pytest.mark.asyncio
async def test_concurrent_processing(document_processor: DocumentProcessor, test_user: Dict, temp_dir: Path, sample_pdf_content: bytes):
    """Test processing multiple documents concurrently."""
    # Create multiple test documents
    docs = []
    for i in range(3):
        test_file = temp_dir / f"test_{i}.pdf"
        test_file.write_bytes(sample_pdf_content)
        
        doc = await document_processor.create_document(
            user_id=test_user["id"],
            filename=f"test_{i}.pdf",
            file_path=str(test_file)
        )
        docs.append(doc)
    
    # Process documents concurrently
    tasks = [document_processor.process_document(doc) for doc in docs]
    processed_docs = await asyncio.gather(*tasks)
    
    assert len(processed_docs) == len(docs)
    for doc in processed_docs:
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.metadata.get("chunk_count") > 0 