# Active Context

## Current Focus
-   Establishing the core FastAPI application structure.
-   Defining database models (e.g., using SQLAlchemy) for template metadata (name, description, storage path, variables).
-   Implementing initial API endpoints for template CRUD operations (Create, Read - List/Get, potentially Update/Delete).
-   Setting up basic Slack integration (Bot token configuration, initial event listener/command handler).
-   Implementing file upload logic and storing templates (initially local file system).

## Recent Changes
-   Reviewed and updated all core Memory Bank files (`projectbrief.md`, `productContext.md`, `systemPatterns.md`, `techContext.md`, `activeContext.md`, `progress.md`) to align with the clarified project scope: Document Template Management System.
-   Created the missing `productContext.md` file.
-   Removed focus on RAG-specific features and technologies.
-   Updated database schema (`migrations/001_initial_schema.sql`) to use `document_templates` table instead of `rag_documents`.

## Active Decisions
1.  **Core Stack:** Python 3.11, FastAPI, PostgreSQL, SQLAlchemy (for ORM).
2.  **Template Handling:** Initial support for DOCX, MD, TXT. Using `python-docx` for DOCX parsing. Simple variable syntax `{{variable_name}}`.
3.  **Chat Integration:** Slack using `slack_sdk`.
4.  **Storage:** PostgreSQL for metadata, local filesystem volume mount for template files (Phase 1).
5.  **Deployment:** Docker / Docker Compose for local development and initial deployment.

## Next Steps (Phase 1 Implementation)
1.  **Database:** Finalize and apply database migrations for the `document_templates` table.
2.  **API:** Implement FastAPI routers and endpoints for:
    *   `POST /templates/`: Upload a template file, extract variables, save metadata to DB, save file to storage.
    *   `GET /templates/`: List available templates.
    *   `GET /templates/{template_id}`: Get details of a specific template.
3.  **Variable Extraction:** Implement logic to parse uploaded templates and identify `{{variable_name}}` placeholders.
4.  **Slack Integration:**
    *   Configure Slack bot token and necessary permissions.
    *   Set up a basic FastAPI endpoint to receive Slack events/commands.
    *   Implement a simple handler for a test command (e.g., `/docgen ping`).
5.  **Testing:** Add basic unit/integration tests for API endpoints and variable extraction.

## Current Considerations
-   Error handling for file uploads and processing.
-   Security implications of storing/executing templates.
-   Defining a clear structure for storing template files.
-   Async handling for potentially long-running Slack interactions or document generation.
-   Refining the exact requirements for template metadata.

## Known Issues
-   None currently identified related to the new focus.

## Dependencies
-   FastAPI, Uvicorn
-   SQLAlchemy, Psycopg2 (or async equivalent like asyncpg)
-   python-docx
-   slack_sdk
-   Docker, Docker Compose 