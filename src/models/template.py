from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Template(BaseModel):
    """Template model for document templates"""
    name: str = Field(..., description="Name of the template")
    path: str = Field(..., description="Path to the template file")
    description: str = Field(..., description="Description of the template")
    variables: Optional[List[str]] = Field(default=None, description="List of variables in the template")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Template last update timestamp")
    version: str = Field(default="1.0.0", description="Template version")
    metadata: dict = Field(default_factory=dict, description="Additional template metadata") 