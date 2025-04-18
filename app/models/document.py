from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    content: str
    filename: str
    file_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    user_id: str

class Document(DocumentBase):
    id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentSearch(BaseModel):
    query: str
    user_id: str
    match_threshold: float = 0.7
    match_count: int = 5 