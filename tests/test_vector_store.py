import pytest
from typing import List, Dict, Any
import numpy as np
from uuid import UUID
from supabase import create_client
from openai import OpenAI
import os
from dotenv import load_dotenv

from services.vector_store import VectorStore
from models.chunks import Chunk, ChunkCreate

load_dotenv()

@pytest.fixture
def supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

@pytest.fixture
def openai_client():
    return OpenAI()

@pytest.fixture
def vector_store(db_session):
    return VectorStore(db_session)

@pytest.fixture
def sample_chunks(test_document, mock_embeddings) -> List[Dict[str, Any]]:
    """Create sample chunks with embeddings."""
    return [
        {
            "id": UUID('12345678-1234-5678-1234-567812345678'),
            "document_id": test_document["id"],
            "user_id": test_document["user_id"],
            "content": f"Sample content {i}",
            "embedding": mock_embeddings,
            "metadata": {"chunk_index": i}
        }
        for i in range(5)
    ]

@pytest.mark.asyncio
async def test_store_chunks(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]]):
    """Test storing chunks with embeddings."""
    stored_chunks = await vector_store.store_chunks(sample_chunks)
    
    assert len(stored_chunks) == len(sample_chunks)
    for chunk in stored_chunks:
        assert isinstance(chunk, Chunk)
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1536

@pytest.mark.asyncio
async def test_similarity_search(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]], mock_embeddings: List[float]):
    """Test similarity search functionality."""
    # Store chunks first
    await vector_store.store_chunks(sample_chunks)
    
    # Perform similarity search
    query_embedding = mock_embeddings
    results = await vector_store.similarity_search(
        user_id=sample_chunks[0]["user_id"],
        query_embedding=query_embedding,
        limit=3
    )
    
    assert len(results) <= 3
    for result in results:
        assert isinstance(result["chunk"], Chunk)
        assert isinstance(result["score"], float)
        assert 0 <= result["score"] <= 1

@pytest.mark.asyncio
async def test_batch_similarity_search(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]], mock_embeddings: List[float]):
    """Test batch similarity search functionality."""
    # Store chunks first
    await vector_store.store_chunks(sample_chunks)
    
    # Create multiple query embeddings
    query_embeddings = [mock_embeddings for _ in range(3)]
    
    # Perform batch similarity search
    results = await vector_store.batch_similarity_search(
        user_id=sample_chunks[0]["user_id"],
        query_embeddings=query_embeddings,
        limit=2
    )
    
    assert len(results) == len(query_embeddings)
    for batch_result in results:
        assert len(batch_result) <= 2
        for result in batch_result:
            assert isinstance(result["chunk"], Chunk)
            assert isinstance(result["score"], float)
            assert 0 <= result["score"] <= 1

@pytest.mark.asyncio
async def test_delete_document_chunks(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]]):
    """Test deleting chunks for a specific document."""
    # Store chunks first
    await vector_store.store_chunks(sample_chunks)
    
    # Delete chunks for the document
    document_id = sample_chunks[0]["document_id"]
    deleted_count = await vector_store.delete_document_chunks(document_id)
    
    assert deleted_count > 0
    
    # Verify chunks are deleted
    remaining_chunks = await vector_store.get_document_chunks(document_id)
    assert len(remaining_chunks) == 0

@pytest.mark.asyncio
async def test_get_document_chunks(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]]):
    """Test retrieving chunks for a specific document."""
    # Store chunks first
    await vector_store.store_chunks(sample_chunks)
    
    # Get chunks for the document
    document_id = sample_chunks[0]["document_id"]
    chunks = await vector_store.get_document_chunks(document_id)
    
    assert len(chunks) == len(sample_chunks)
    for chunk in chunks:
        assert chunk.document_id == document_id
        assert chunk.embedding is not None

@pytest.mark.asyncio
async def test_update_chunk_metadata(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]]):
    """Test updating chunk metadata."""
    # Store chunks first
    stored_chunks = await vector_store.store_chunks(sample_chunks)
    
    # Update metadata for a chunk
    chunk_id = stored_chunks[0].id
    new_metadata = {"updated": True, "chunk_index": 0}
    updated_chunk = await vector_store.update_chunk_metadata(chunk_id, new_metadata)
    
    assert updated_chunk.metadata == new_metadata

@pytest.mark.asyncio
async def test_user_isolation(vector_store: VectorStore, sample_chunks: List[Dict[str, Any]], test_user: Dict):
    """Test that users can only access their own chunks."""
    # Store chunks for the original user
    await vector_store.store_chunks(sample_chunks)
    
    # Create a different user
    other_user_id = UUID('98765432-9876-5432-9876-987654321098')
    
    # Try to access chunks with different user
    results = await vector_store.similarity_search(
        user_id=other_user_id,
        query_embedding=sample_chunks[0]["embedding"],
        limit=3
    )
    
    assert len(results) == 0  # Should not find any chunks for different user

@pytest.mark.asyncio
async def test_error_handling(vector_store: VectorStore):
    """Test error handling for invalid operations."""
    # Try to store invalid chunks
    invalid_chunks = [{"invalid": "data"}]
    with pytest.raises(Exception):
        await vector_store.store_chunks(invalid_chunks)
    
    # Try to search with invalid embedding
    with pytest.raises(Exception):
        await vector_store.similarity_search(
            user_id=UUID('12345678-1234-5678-1234-567812345678'),
            query_embedding=[0.1],  # Invalid dimension
            limit=3
        )

async def test_vector_store_operations(supabase_client, openai_client):
    # Test data
    test_content = "This is a test document for vector operations."
    test_user_id = "test_user"
    
    # Generate embedding
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=test_content
    )
    embedding = response.data[0].embedding
    
    # Insert into Supabase
    result = await supabase_client.table('documents').insert({
        "content": test_content,
        "embedding": embedding,
        "user_id": test_user_id,
        "filename": "test.txt",
        "file_type": "text/plain",
        "metadata": {"test": True}
    }).execute()
    
    assert result.data is not None
    
    # Test search
    search_result = await supabase_client.rpc(
        'match_documents',
        {
            "query_embedding": embedding,
            "match_threshold": 0.7,
            "match_count": 1,
            "p_user_id": test_user_id
        }
    ).execute()
    
    assert len(search_result.data) > 0
    assert search_result.data[0]["content"] == test_content
    
    # Cleanup
    await supabase_client.table('documents').delete().eq("user_id", test_user_id).execute()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 