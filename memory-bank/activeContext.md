# Active Context

## Current Focus
- Project structure cleanup and organization
- Consolidating services into app/services directory
- Maintaining clean architecture with Supabase integration
- Setting up proper template management with background processing

## Recent Changes
- Consolidated all services into app/services directory
- Merged template repository functionality into TemplateProcessor service
- Removed unnecessary directories (migrations, database, src, etc.)
- Cleaned up project structure for better maintainability
- Implemented async template processing with background tasks

## Active Decisions
1. **Core Stack:** Python 3.11, FastAPI, Supabase (vector database)
2. **Project Structure:**
   - All services consolidated in app/services
   - Clean separation of concerns with models and services
   - Template storage in /templates directory
   - No local database, using Supabase for storage
3. **Document Processing:** 
   - Using PyPDF2 for PDF processing with async wrapper
   - Using python-docx for DOCX processing with async wrapper
   - Running document processing in thread pool to avoid blocking
   - Implementing safe file handling with size limits (100MB)
4. **Template Management:**
   - Templates stored in /templates directory
   - Metadata stored in JSON format
   - Background processing for template analysis
   - Async operations for better performance
5. **Error Handling:**
   - Specific exception types for different error scenarios
   - Proper error context preservation
   - Validation for file existence and size
6. **Resource Management:**
   - Async file operations with aiofiles
   - Automatic cleanup of temporary files
   - Managed file context for safe processing
7. **API Endpoints:** Two main endpoints - `/file` for document upload and `/chat` for interactions

## Next Steps
1. **Template Processing:**
   - Implement template analysis in background tasks
   - Add template suggestion logic based on document content
   - Enhance template metadata management
2. **Document Processing:**
   - Complete TXT parsing functionality
   - Enhance chunking algorithm for better text segmentation
3. **Supabase Integration:**
   - Setup connection to Supabase for vector storage
   - Implement document chunking and embedding functionality
   - Store processed documents in vector database

## Current Considerations
- Monitoring and logging for template processing
- Memory usage optimization for large templates
- Security implications of template storage
- Performance optimization of async operations
- Ensuring proper cleanup of resources
- Testing coverage for template management

## Known Issues
- None currently identified

## Dependencies
- FastAPI, Uvicorn
- PyPDF2 for PDF processing
- python-docx for DOCX processing
- aiofiles for async file operations
- Supabase client for Python
- OpenAI or similar for embeddings
- Docker, Docker Swarm 