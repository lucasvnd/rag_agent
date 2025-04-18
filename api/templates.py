from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
from uuid import UUID
import shutil
from pathlib import Path
from datetime import datetime

from models.templates import (
    Template,
    TemplateCreate,
    TemplateUpdate,
    TemplateList,
    TemplateResponse
)
from services.template_processor import TemplateProcessor

router = APIRouter(prefix="/templates", tags=["templates"])
template_processor = TemplateProcessor()

# Directory for storing template files
TEMPLATE_DIR = Path("templates")
TEMPLATE_DIR.mkdir(exist_ok=True)

@router.post("/upload", response_model=TemplateResponse)
async def upload_template(
    name: str,
    description: str = None,
    file: UploadFile = File(...)
) -> TemplateResponse:
    """Upload a new template file"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    # Save the template file
    file_path = TEMPLATE_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create template record
    template = Template(
        id=UUID(int=0),  # This would normally come from your database
        name=name,
        description=description,
        file_path=str(file_path),
        version=1,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={},
        user_id=UUID(int=0)  # This would normally be the authenticated user's ID
    )
    
    # Extract variables from template
    variables = await template_processor.get_template_variables(template)
    template.metadata = await template_processor.update_template_metadata(template, variables)
    
    return TemplateResponse(
        template=template,
        message="Template uploaded successfully"
    )

@router.get("/list", response_model=TemplateList)
async def list_templates() -> TemplateList:
    """List all available templates"""
    templates = []
    for file_path in TEMPLATE_DIR.glob("*.docx"):
        template = Template(
            id=UUID(int=0),  # This would normally come from your database
            name=file_path.stem,
            file_path=str(file_path),
            version=1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
            user_id=UUID(int=0)  # This would normally be the authenticated user's ID
        )
        # Extract variables
        variables = await template_processor.get_template_variables(template)
        template.metadata = await template_processor.update_template_metadata(template, variables)
        templates.append(template)
    
    return TemplateList(templates=templates)

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: UUID) -> TemplateResponse:
    """Get template details by ID"""
    # In a real implementation, you would fetch this from a database
    # For now, we'll just list all templates and find the matching one
    templates = await list_templates()
    for template in templates.templates:
        if template.id == template_id:
            return TemplateResponse(
                template=template,
                message="Template retrieved successfully"
            )
    raise HTTPException(status_code=404, detail="Template not found")

@router.post("/{template_id}/process")
async def process_template(
    template_id: UUID,
    data: Dict[str, Any]
) -> Dict[str, str]:
    """Process a template with provided data"""
    # Get the template
    templates = await list_templates()
    template = next((t for t in templates.templates if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Process the template
    try:
        # Validate and process the template
        doc = await template_processor.process_template(template, data)
        
        # Save the processed file with a unique name
        output_filename = f"processed_{template.name}_{datetime.utcnow().timestamp()}.docx"
        output_path = TEMPLATE_DIR / output_filename
        await template_processor.save_processed_template(doc, str(output_path))
        
        return {
            "message": "Template processed successfully",
            "output_file": str(output_path)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing template: {str(e)}")

@router.delete("/{template_id}", response_model=Dict[str, str])
async def delete_template(template_id: UUID) -> Dict[str, str]:
    """Delete a template"""
    # Get the template
    templates = await list_templates()
    template = next((t for t in templates.templates if t.id == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        # Delete the template file
        template_path = Path(template.file_path)
        if template_path.exists():
            template_path.unlink()
        return {"message": "Template deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}") 