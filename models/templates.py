from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from uuid import UUID

class TemplateBase(BaseModel):
    """Base template model"""
    name: str
    description: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

class TemplateCreate(TemplateBase):
    """Model for creating a new template"""
    file_path: str

class TemplateUpdate(BaseModel):
    """Model for updating a template"""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict] = None
    is_active: Optional[bool] = None

class Template(BaseModel):
    """
    Model representing a document template
    """
    id: str
    name: str
    description: Optional[str] = None
    file_path: str
    variables: Dict[str, str]  # Variable name -> description mapping
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TemplateList(BaseModel):
    """Model for list of templates"""
    templates: List[Template]

class TemplateResponse(BaseModel):
    """Response model for template operations"""
    template: Template
    message: str 