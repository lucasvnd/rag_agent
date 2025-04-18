from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import List
from services.document_processor import process_document, get_processing_status
from services.background_tasks import add_document_processing_task
from models.schemas import FileResponse, FileStatus
from security.auth import get_current_user
import uuid

router = APIRouter()

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_id: str = Depends(get_current_user)
):
    """
    Upload a document (PDF/DOCX) for processing
    """
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )
    
    try:
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        # Add processing task to background tasks
        add_document_processing_task(background_tasks, file_id, user_id)
        
        return FileResponse(
            file_id=file_id,
            filename=file.filename,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/{file_id}", response_model=FileStatus)
async def get_file_status(
    file_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get the processing status of a file
    """
    try:
        # Get status from database
        status = await get_processing_status(file_id, user_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {str(e)}"
        ) 