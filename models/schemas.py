from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FileResponse(BaseModel):
    """Response model for file upload"""
    file_id: str
    filename: str
    status: str

class FileStatus(BaseModel):
    """Status model for file processing"""
    file_id: str
    filename: str
    status: str
    chunks_processed: int = 0
    total_chunks: Optional[int] = None
    error: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for chat endpoints"""
    query: str
    template_id: Optional[str] = None
    context_window: int = 5

class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    answer: str
    sources: List[Dict[str, Any]]
    template_used: Optional[str] = None

class ProcessedChunk(BaseModel):
    """Model for processed document chunks"""
    chunk_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]

class ProcessedDocument(BaseModel):
    """Model for processed documents"""
    file_id: str
    filename: str
    chunks: List[ProcessedChunk]
    metadata: Dict[str, Any] 