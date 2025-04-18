# Active Context

## Current Focus
-   Finalizing project scope alignment across all documentation and code.
-   Setting up testing infrastructure for all core components using pytest.
-   Implementing test-driven development practices for document processing and API endpoints.
-   Setting up Supabase integration for vector storage of processed documents.
-   Implementing document processing, chunking, and embedding functionality.
-   Maintaining version control through GitHub with systematic commits.
-   Preparing API structure for the `/file` and `/chat` endpoints.

## Recent Changes
-   Established comprehensive testing infrastructure with unit, integration, and API tests.
-   Set up GitHub Actions workflow for continuous integration testing.
-   Created detailed testing strategy documentation for the project.
-   Implemented test fixtures and mock objects for Supabase and document processing.
-   Updated Git workflow with feature branches, conventional commits, and pull requests.
-   Reviewed and updated all core Memory Bank files to align with the clarified project scope: Document processing with RAG and template suggestion.
-   Updated database approach to use Supabase vector store for document storage.
-   Corrected the API endpoint structure to focus on `/file` and `/chat` endpoints.
-   Removed irrelevant code and files that were not aligned with the project scope.
-   Committed all changes to GitHub with descriptive commit messages.

## Active Decisions
1.  **Core Stack:** Python 3.11, FastAPI, Supabase (vector database).
2.  **Document Processing:** Support for document formats like DOCX, PDF, TXT using appropriate libraries.
3.  **Template Storage:** Templates stored in the /templates directory, deployed with the Docker container.
4.  **API Endpoints:** Two main endpoints - `/file` for document upload and `/chat` for interactions.
5.  **Deployment:** Docker Swarm on VPS for production deployment.
6.  **Version Control:** 
    * GitHub repository (lucasvnd/rag_agent) with protected main branch
    * Feature branch workflow for all changes
    * Pull request reviews before merging to main
    * Descriptive commit messages following conventional commits format
    * Regular commits for incremental changes

## Next Steps (Phase 1 Implementation)
1.  **Testing Framework Implementation:**
    *   Develop actual implementation to pass the existing tests.
    *   Follow test-driven development principles.
    *   Add additional test cases as needed.
2.  **Supabase Integration:**
    *   Setup connection to Supabase for vector storage.
    *   Implement document chunking and embedding functionality.
    *   Store processed documents in Supabase vector database.
3.  **API Implementation:**
    *   Implement logic for `POST /file`: Handle document upload, processing, chunking, and storage.
    *   Implement logic for `POST /chat`: Process user queries against stored documents.
4.  **Document Analysis:**
    *   Implement logic to analyze document content.
    *   Develop algorithm to suggest appropriate templates from the /templates directory.
5.  **Template Management:**
    *   Organize and catalog existing templates in the /templates directory.
    *   Implement logic to access and utilize templates for suggestions.
5.  **Testing:** Add basic unit/integration tests for API endpoints and document processing.

## Current Considerations
-   Error handling for document uploads and processing.
-   Security implications of storing and processing documents.
-   Optimizing chunking and embedding processes for performance.
-   Ensuring proper integration with Supabase.
-   Defining appropriate algorithms for template suggestion based on document content.
-   Maintaining clear version control with descriptive commits.

## Known Issues
-   None currently identified related to the new focus.

## Dependencies
-   FastAPI, Uvicorn
-   Supabase client for Python
-   Document processing libraries (python-docx, PyPDF2/pdfplumber)
-   OpenAI or similar for embeddings
-   Docker, Docker Swarm
-   Git/GitHub for version control 