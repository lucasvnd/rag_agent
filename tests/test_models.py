import pytest
from datetime import datetime
from models.templates import Template, TemplateCreate, TemplateUpdate
from pydantic import ValidationError

def test_template_create():
    """Test creating a template with valid data"""
    template_data = {
        "name": "Test Template",
        "description": "A test template",
        "file_path": "/templates/test.docx"
    }
    template = TemplateCreate(**template_data)
    assert template.name == "Test Template"
    assert template.description == "A test template"
    assert template.file_path == "/templates/test.docx"
    assert template.metadata == {}

def test_template_create_required_fields():
    """Test that required fields are enforced"""
    with pytest.raises(ValidationError):
        TemplateCreate()  # No fields provided
    
    with pytest.raises(ValidationError):
        TemplateCreate(description="Test")  # Missing name and file_path

def test_template_model():
    """Test the main Template model"""
    template_data = {
        "id": "123",
        "name": "Test Template",
        "description": "A test template",
        "file_path": "/templates/test.docx",
        "variables": {"name": "string", "age": "integer"},
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    template = Template(**template_data)
    assert template.id == "123"
    assert template.name == "Test Template"
    assert template.variables == {"name": "string", "age": "integer"}

def test_template_update():
    """Test template update model"""
    # Test partial update
    update_data = {"name": "Updated Name"}
    update = TemplateUpdate(**update_data)
    assert update.name == "Updated Name"
    assert update.description is None
    assert update.metadata is None
    
    # Test full update
    full_update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "metadata": {"version": "2.0"},
        "is_active": True
    }
    update = TemplateUpdate(**full_update_data)
    assert update.name == "Updated Name"
    assert update.description == "Updated description"
    assert update.metadata == {"version": "2.0"}
    assert update.is_active is True

def test_template_validation():
    """Test template validation rules"""
    # Test invalid variables format
    with pytest.raises(ValidationError):
        Template(
            id="123",
            name="Test",
            file_path="/test.docx",
            variables="invalid",  # Should be a dict
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    # Test invalid dates
    with pytest.raises(ValidationError):
        Template(
            id="123",
            name="Test",
            file_path="/test.docx",
            variables={},
            created_at="invalid",  # Should be datetime
            updated_at=datetime.now()
        ) 