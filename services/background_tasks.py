from fastapi import BackgroundTasks
from typing import Dict, Any
import asyncio
from services.document_processor import process_document
from services.vector_store import VectorStore

class DocumentProcessingTask:
    """
    Background task for processing documents
    """
    
    def __init__(self, file_id: str, user_id: str):
        self.file_id = file_id
        self.user_id = user_id
    
    async def __call__(self):
        """
        Process the document in the background
        """
        try:
            # Update status to processing
            await VectorStore.update_document_status(self.file_id, "processing")
            
            # Process the document
            await process_document(self.file_id, self.user_id)
            
            # Update status to completed
            await VectorStore.update_document_status(self.file_id, "completed")
            
        except Exception as e:
            # Update status to error
            await VectorStore.update_document_status(
                self.file_id,
                "error",
                str(e)
            )
            raise e

def add_document_processing_task(
    background_tasks: BackgroundTasks,
    file_id: str,
    user_id: str
) -> None:
    """
    Add a document processing task to the background tasks queue
    """
    task = DocumentProcessingTask(file_id, user_id)
    background_tasks.add_task(task) 