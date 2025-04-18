# Active Context

## Current Focus
- Improving and hardening the document processing functionality
- Implementing proper async/sync operations in document processing
- Enhancing error handling and resource management
- Setting up Supabase integration for vector storage of processed documents

## Recent Changes
- Enhanced PDF processing with proper async/sync operations
- Improved error handling with specific exception types
- Added resource management for temporary files
- Implemented file size limits and validation
- Added async file operations using aiofiles
- Added proper cleanup of temporary processing files

## Active Decisions
1. **Core Stack:** Python 3.11, FastAPI, Supabase (vector database)
2. **Document Processing:** 
   - Using PyPDF2 for PDF processing with async wrapper
   - Running PDF processing in thread pool to avoid blocking
   - Implementing safe file handling with size limits (100MB)
   - Using temporary file management for processing
3. **Error Handling:**
   - Specific exception types for different error scenarios
   - Proper error context preservation
   - Validation for file existence and size
4. **Resource Management:**
   - Async file operations with aiofiles
   - Automatic cleanup of temporary files
   - Managed file context for safe processing
5. **Template Storage:** Templates stored in the /templates directory, deployed with the Docker container
6. **API Endpoints:** Two main endpoints - `/file` for document upload and `/chat` for interactions
7. **Deployment:** Docker Swarm on VPS for production deployment

## Next Steps (Phase 1 Implementation)
1. **Document Processing:**
   - Implement DOCX parsing functionality
   - Implement TXT parsing functionality
   - Enhance chunking algorithm for better text segmentation
2. **Supabase Integration:**
   - Setup connection to Supabase for vector storage
   - Implement document chunking and embedding functionality
   - Store processed documents in Supabase vector database
3. **API Implementation:**
   - Implement logic for `POST /file`: Handle document upload, processing, chunking, and storage
   - Implement logic for `POST /chat`: Process user queries against stored documents

## Current Considerations
- Monitoring and logging for file processing operations
- Memory usage optimization for large files
- Security implications of temporary file storage
- Performance optimization of async operations
- Ensuring proper cleanup of resources
- Defining appropriate algorithms for template suggestion based on document content

## Known Issues
- None currently identified

## Dependencies
- FastAPI, Uvicorn
- PyPDF2 for PDF processing
- aiofiles for async file operations
- Supabase client for Python
- Document processing libraries (python-docx to be implemented)
- OpenAI or similar for embeddings
- Docker, Docker Swarm 