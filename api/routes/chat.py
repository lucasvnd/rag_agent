from fastapi import APIRouter, HTTPException, Depends
from models.schemas import ChatRequest, ChatResponse
from services.chat_service import query_documents, generate_from_template
from services.auth import get_current_user

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Query the document database and get relevant information
    """
    try:
        response = await query_documents(
            query=request.query,
            user_id=current_user["user_id"],
            context_window=request.context_window
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/template", response_model=ChatResponse)
async def template(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate a response using a template and document context
    """
    if not request.template_id:
        raise HTTPException(
            status_code=400,
            detail="Template ID is required"
        )
    
    try:
        response = await generate_from_template(
            query=request.query,
            template_id=request.template_id,
            user_id=current_user["user_id"],
            context_window=request.context_window
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        ) 