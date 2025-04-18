# Active Context

## Current Focus
-   Establishing the core FastAPI application structure with two main endpoints: `/file` and `/chat`.
-   Setting up Supabase integration for vector storage of processed documents.
-   Implementing document processing, chunking, and embedding functionality.
-   Setting up the template directory structure with sample templates.
-   Implementing analysis to suggest appropriate templates based on document content.

## Recent Changes
-   Reviewed and updated all core Memory Bank files to align with the clarified project scope: Document processing with RAG and template suggestion.
-   Updated database approach to use Supabase vector store for document storage.
-   Corrected the API endpoint structure to focus on `/file` and `/chat` endpoints.
-   Clarified that templates are stored in the /templates folder and deployed with the Docker container.

## Active Decisions
1.  **Core Stack:** Python 3.11, FastAPI, Supabase (vector database).
2.  **Document Processing:** Support for document formats like DOCX, PDF, TXT using appropriate libraries.
3.  **Template Storage:** Templates stored in the /templates directory, deployed with the Docker container.
4.  **API Endpoints:** Two main endpoints - `/file` for document upload and `/chat` for interactions.
5.  **Deployment:** Docker Swarm on VPS for production deployment.

## Next Steps (Phase 1 Implementation)
1.  **Supabase Integration:**
    *   Setup connection to Supabase for vector storage.
    *   Implement document chunking and embedding functionality.
    *   Store processed documents in Supabase vector database.
2.  **API Implementation:**
    *   Implement logic for `POST /file`: Handle document upload, processing, chunking, and storage.
    *   Implement logic for `POST /chat`: Process user queries against stored documents.
3.  **Document Analysis:**
    *   Implement logic to analyze document content.
    *   Develop algorithm to suggest appropriate templates from the /templates directory.
4.  **Template Management:**
    *   Organize and catalog existing templates in the /templates directory.
    *   Implement logic to access and utilize templates for suggestions.
5.  **Testing:** Add basic unit/integration tests for API endpoints and document processing.

## Current Considerations
-   Error handling for document uploads and processing.
-   Security implications of storing and processing documents.
-   Optimizing chunking and embedding processes for performance.
-   Ensuring proper integration with Supabase.
-   Defining appropriate algorithms for template suggestion based on document content.

## Known Issues
-   None currently identified related to the new focus.

## Dependencies
-   FastAPI, Uvicorn
-   Supabase client for Python
-   Document processing libraries (python-docx, PyPDF2/pdfplumber)
-   OpenAI or similar for embeddings
-   Docker, Docker Swarm 