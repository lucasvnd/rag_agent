# Project Progress

## What Works

### Foundational Setup
1.  **Project Structure:** Basic FastAPI project layout established.
2.  **Version Control:** Git repository setup on GitHub.
3.  **Memory Bank:** All core memory bank files exist, have been reviewed, and updated to reflect the Document Template Management System scope.
4.  **Containerization:** Basic Dockerfile and `docker-compose.yml` exist (may need adjustments for new services like DB).
5.  **Database Schema:** Initial migration created and updated to define the `document_templates` table (replacing `rag_documents`).

## Current Status (Phase 1 In Progress)

### Core Application Setup
1.  **FastAPI Application:** Initializing the main app instance, setting up basic configuration.
2.  **Database Models:** Defining SQLAlchemy models for `DocumentTemplate` (metadata: id, name, description, file_path, variables, created_at, updated_at).
3.  **API Endpoints (Structure):** Setting up API routers for `/templates`.
4.  **Slack Integration (Setup):** Configuring bot token and basic connection verification (pending implementation of actual handlers).
5.  **File Handling (Concept):** Planning local file storage structure (`./templates_data/` volume mount).

## What's Left to Build

### Phase 1: Core Functionality
1.  **Database Implementation:**
    *   Finalize SQLAlchemy models.
    *   Implement database session management.
    *   Apply migrations to create the table in the actual DB.
2.  **API Implementation:**
    *   Implement logic for `POST /templates/`: Handle file upload, save file, extract variables, save metadata to DB.
    *   Implement logic for `GET /templates/`: Query DB and return list of templates.
    *   Implement logic for `GET /templates/{template_id}`: Query DB for specific template details.
    *   Add basic error handling and validation.
3.  **Variable Extraction:**
    *   Implement function to parse DOCX files (using `python-docx`) for `{{variable}}` patterns.
    *   Implement similar logic for MD/TXT files.
    *   Store extracted variable names in the DB record.
4.  **Basic Slack Integration:**
    *   Implement handler for `/docgen ping` or similar test command.
    *   Set up endpoint to receive Slack events (e.g., for slash commands).
5.  **Initial Testing:** Unit tests for variable extraction, basic integration tests for API endpoints.

### Phase 2: Chat Interaction & Generation
1.  **Slack Command Implementation:**
    *   `/docgen list templates`: Fetch list from API and display in Slack.
    *   `/docgen create <template_name>`: Initiate the generation flow.
2.  **Interactive Chat Flow:**
    *   Retrieve required variables for the selected template.
    *   Sequentially prompt the user in Slack for each variable's value.
    *   Store user responses temporarily.
3.  **Document Generation Logic:**
    *   Retrieve template file content.
    *   Perform variable replacement using collected values.
    *   Handle different file types (DOCX, MD, TXT).
4.  **Result Delivery:**
    *   Save the generated document.
    *   Provide the document back to the user in Slack (e.g., as an attachment or download link).
5.  **Enhanced Error Handling:** For chat interactions and document generation.

### Phase 3: Refinements & Future Features
1.  **Advanced Template Features:** Versioning, more complex variable types, conditional logic (if using Jinja2).
2.  **User Management:** Authentication/Authorization (if needed beyond Slack user identity).
3.  **Security Hardening:** Rate limiting, input sanitization, dependency scanning.
4.  **Deployment:** Production-ready deployment configuration (Swarm/K8s), monitoring, logging aggregation.
5.  **Scalability & Performance:** Optimization, potential async processing for generation.
6.  **Cloud Storage:** Integration with S3/GCS for template files.
7.  **UI:** Potential simple web UI for template management.

## Known Issues
-   None identified specific to the current implementation phase.

## Next Steps (Immediate Priority - Phase 1)
-   Finalize DB models and migrations.
-   Implement core API endpoint logic (Upload, List).
-   Implement variable extraction for DOCX/TXT/MD.
-   Setup basic Slack command endpoint and test handler.

# API Keys
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Configuration
MAX_FILE_SIZE=10485760  # 10MB for example
CHUNK_SIZE=500
CHUNK_OVERLAP=50
EMBEDDING_MODEL=text-embedding-ada-002

# Security
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

-- Enable vector extension if not enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Create index for vector similarity search
CREATE INDEX ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    p_user_id TEXT
)
RETURNS TABLE (
    id bigint,
    content text,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        1 - (documents.embedding <=> query_embedding) as similarity,
        documents.metadata
    FROM documents
    WHERE 
        documents.user_id = p_user_id
        AND 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    supabase_url: str
    supabase_key: str
    
    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Processing
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    chunk_size: int = 500
    chunk_overlap: int = 50
    allowed_file_types: set = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    
    # Vector Store
    embedding_dimension: int = 1536
    match_threshold: float = 0.7
    max_results: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings() 