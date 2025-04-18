import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from models.schemas import ProcessedChunk, FileStatus

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

class VectorStore:
    """
    Handles vector storage operations using Supabase's vector store
    """
    
    @staticmethod
    async def store_document(
        file_id: str,
        user_id: str,
        filename: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Store document metadata in the documents table
        """
        try:
            supabase.table("documents").insert({
                "id": file_id,
                "user_id": user_id,
                "filename": filename,
                "status": "processing",
                "metadata": metadata
            }).execute()
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            raise e

    @staticmethod
    async def store_chunk(chunk: ProcessedChunk, user_id: str, document_id: str) -> None:
        """
        Store a document chunk with its embedding in the chunks table
        """
        try:
            supabase.table("chunks").insert({
                "id": chunk.chunk_id,
                "document_id": document_id,
                "user_id": user_id,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata
            }).execute()
        except Exception as e:
            print(f"Error storing chunk: {str(e)}")
            raise e

    @staticmethod
    async def update_document_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update the processing status of a document
        """
        try:
            data = {"status": status}
            if error_message:
                data["error_message"] = error_message
            
            supabase.rpc(
                "update_document_status",
                {
                    "doc_id": document_id,
                    "new_status": status,
                    "error_msg": error_message
                }
            ).execute()
        except Exception as e:
            print(f"Error updating document status: {str(e)}")
            raise e

    @staticmethod
    async def get_document_status(document_id: str, user_id: str) -> FileStatus:
        """
        Get the processing status of a document
        """
        try:
            result = supabase.table("documents") \
                .select("id, filename, status, metadata, error_message") \
                .eq("id", document_id) \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if not result.data:
                raise Exception("Document not found")
            
            doc = result.data
            chunks_result = supabase.table("chunks") \
                .select("id") \
                .eq("document_id", document_id) \
                .execute()
            
            return FileStatus(
                file_id=doc["id"],
                filename=doc["filename"],
                status=doc["status"],
                chunks_processed=len(chunks_result.data) if chunks_result.data else 0,
                total_chunks=doc["metadata"].get("chunk_count", 0),
                error=doc.get("error_message")
            )
        except Exception as e:
            print(f"Error getting document status: {str(e)}")
            raise e

    @staticmethod
    async def search_similar(
        query_embedding: List[float],
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity
        """
        try:
            filter_metadata = filter_metadata or {}
            result = supabase.rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "user_id": user_id,
                    "match_count": limit,
                    "similarity_threshold": similarity_threshold,
                    "filter": filter_metadata
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching similar chunks: {str(e)}")
            raise e

    @staticmethod
    async def search_text(
        query_text: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks using text similarity
        """
        try:
            result = supabase.rpc(
                "search_chunks_by_text",
                {
                    "query_text": query_text,
                    "user_id": user_id,
                    "match_count": limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error searching chunks by text: {str(e)}")
            raise e 