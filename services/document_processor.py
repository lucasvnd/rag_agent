import asyncio
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from datetime import datetime
import aiofiles
import os
from contextlib import asynccontextmanager

from models.documents import Document, DocumentCreate, DocumentStatus, DocumentChunk

class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""
    pass

class FileNotFoundError(DocumentProcessingError):
    """Raised when the document file is not found."""
    pass

class InvalidFileError(DocumentProcessingError):
    """Raised when the document file is invalid or corrupted."""
    pass

class FileSizeError(DocumentProcessingError):
    """Raised when the document file exceeds size limits."""
    pass

class DocumentProcessor:
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __init__(self, db_session, temp_dir: Path):
        self.db_session = db_session
        self.temp_dir = temp_dir
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def _managed_file(self, file_path: str):
        """Context manager for handling file operations with proper cleanup."""
        temp_path = None
        try:
            # Copy file to temp directory for processing
            temp_path = self.temp_dir / f"proc_{datetime.utcnow().timestamp()}_{Path(file_path).name}"
            await self._copy_to_temp(file_path, temp_path)
            yield temp_path
        finally:
            # Cleanup temp file
            if temp_path and temp_path.exists():
                temp_path.unlink()

    async def _copy_to_temp(self, src_path: str, dest_path: Path) -> None:
        """Copy file to temporary location asynchronously."""
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"File not found: {src_path}")

        # Check file size
        file_size = os.path.getsize(src_path)
        if file_size > self.MAX_FILE_SIZE:
            raise FileSizeError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)")

        async with aiofiles.open(src_path, 'rb') as src, \
                   aiofiles.open(dest_path, 'wb') as dest:
            await dest.write(await src.read())

    async def create_document(self, user_id: str, filename: str, file_path: str) -> Document:
        """Create a new document record."""
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path
        )
        return doc

    async def process_document(self, document: Document) -> Document:
        """Process a document and generate chunks."""
        try:
            document.status = DocumentStatus.PROCESSING
            
            # Generate chunks from the document
            chunks = await self.generate_chunks(document)
            
            # Update document metadata
            document.metadata.update({
                "chunk_count": len(chunks),
                "processed_at": datetime.utcnow().isoformat(),
                "file_size": os.path.getsize(document.file_path)
            })
            
            document.status = DocumentStatus.COMPLETED
            
        except FileNotFoundError as e:
            document.status = DocumentStatus.ERROR
            document.error_message = f"File not found: {str(e)}"
        except InvalidFileError as e:
            document.status = DocumentStatus.ERROR
            document.error_message = f"Invalid file: {str(e)}"
        except FileSizeError as e:
            document.status = DocumentStatus.ERROR
            document.error_message = f"File size error: {str(e)}"
        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.error_message = f"Processing error: {str(e)}"
        
        return document

    async def generate_chunks(self, document: Document) -> List[DocumentChunk]:
        """Generate chunks from a document."""
        if document.filename.lower().endswith('.pdf'):
            return await self._process_pdf(document)
        else:
            raise ValueError(f"Unsupported file type: {document.filename}")

    async def _process_pdf(self, document: Document) -> List[DocumentChunk]:
        """Process a PDF document and return chunks."""
        chunks = []
        
        async with self._managed_file(document.file_path) as temp_path:
            try:
                # Process PDF in a separate thread to avoid blocking
                loop = asyncio.get_event_loop()
                chunks = await loop.run_in_executor(None, self._process_pdf_sync, document, temp_path)
                return chunks
            except PyPDF2.PdfReadError as e:
                raise InvalidFileError(f"Invalid PDF file: {str(e)}")
            except Exception as e:
                raise DocumentProcessingError(f"Error processing PDF: {str(e)}")

    def _process_pdf_sync(self, document: Document, file_path: Path) -> List[DocumentChunk]:
        """Synchronous PDF processing to be run in a thread pool."""
        chunks = []
        with open(file_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Update document metadata
                document.metadata.update({
                    "page_count": len(pdf_reader.pages),
                    "pdf_version": pdf_reader.pdf_version
                })
                
                # Process each page
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    # Skip empty pages
                    if not text.strip():
                        continue
                    
                    # Create chunk for the page
                    chunk = DocumentChunk(
                        document_id=document.id,
                        user_id=document.user_id,
                        content=text,
                        metadata={
                            "page_number": page_num + 1,
                            "source": "pdf"
                        }
                    )
                    chunks.append(chunk)
                
                return chunks
                
            except Exception as e:
                raise DocumentProcessingError(f"Error processing PDF: {str(e)}")

    async def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for chunks."""
        # This will be implemented later when we integrate with OpenAI
        return chunks 