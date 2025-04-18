from enum import Enum
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
import uuid

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class DocumentBase(BaseModel):
    filename: str
    file_path: str
    metadata: Dict = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    user_id: str

class Document(DocumentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    user_id: str
    content: str
    metadata: Dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True 