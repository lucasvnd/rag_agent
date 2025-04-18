# Technical Context

## Core Technologies
-   **Programming Language:** Python 3.11+
-   **Web Framework:** FastAPI
-   **Vector Database:** Supabase with pgvector extension
-   **Document Processing Libs:**
    -   `python-docx` (for DOCX manipulation)
    -   `PyPDF2` or `pdfplumber` (for PDF processing)
    -   Standard text/string formatting (for TXT)
-   **Document Storage:** Supabase with vector embeddings
-   **Template Storage:** Local filesystem via Docker volume
-   **Containerization:** Docker
-   **Orchestration:** Docker Swarm (for deployment on VPS)
-   **Reverse Proxy/Gateway:** Traefik (for routing)

## Development Environment
-   Python 3.11
-   Docker Engine 24.x+
-   Docker Compose v2
-   Docker Swarm mode
-   Traefik v2.x for routing
-   IDE: VS Code / Cursor
-   Version Control: Git / GitHub

## Container Infrastructure
1.  **Base Image**
    *   `python:3.11-slim`
    *   Multi-stage build for optimization

2.  **Resource Configuration (Example)**
    *   CPU: 1 core limit, 0.5 core reservation
    *   Memory: 1GB limit, 512MB reservation
    *   *Needs adjustment based on actual load*

3.  **Networking**
    *   Docker network (bridge for Compose, overlay for Swarm)
    *   Internal service discovery
    *   Traefik integration for routing
    *   Health check endpoints (`/health`)

4.  **Storage**
    *   **Supabase:** External vector database for document storage and embeddings.
    *   **Template Storage:** Volume mount for local template files (/templates directory).
    *   **Logging:** stdout/stderr captured by Docker, potentially volume for log files if needed.

## Deployment Architecture
1.  **Orchestration:** Docker Swarm for deployment on VPS
    *   Document Processing Service container
    *   Optional: Traefik container for routing
    *   Configuration via Docker Swarm stack

2. Docker Swarm Setup
   - Single replica (potentially scalable)
   - Rolling updates with health checks
   - Automatic rollback on failure
   - Resource constraints and reservations

3. Service Configuration
   - Environment variables from .env
   - Secrets management (for API keys)
   - Health monitoring
   - Logging and rotation

4. Load Balancing
   - Traefik as reverse proxy
   - Dynamic routing
   - SSL termination
   - Service discovery

## API Endpoints
1. Document Upload
   - Path: `/file`
   - Methods: POST
   - Functionality: Upload documents for processing, chunking, and embedding
   - Authentication: API key or JWT (future implementation)

2. Chat Interaction
   - Path: `/chat`
   - Methods: POST
   - Functionality: Interact with processed documents, analyze content, suggest templates
   - Authentication: API key or JWT (future implementation)

3. Health Monitoring
   - Path: `/health`
   - Methods: GET
   - Functionality: Service health check

## Development Workflow
1. Local Development
   - Docker Compose for development
   - Hot reload enabled
   - Volume mounts for code changes
   - Local environment variables

2. Testing
   - Container-based testing
   - Integration tests with dependencies
   - Health check validation
   - Resource usage monitoring

3. Deployment
   - Manual deployment to Docker Swarm on VPS
   - Version tagging
   - Stack deployment

## Security Considerations
1. Container Security
   - Non-root user
   - Minimal base image
   - No unnecessary packages
   - Regular security updates

2. Network Security
   - Internal network isolation
   - Traefik secure headers
   - Rate limiting
   - SSL/TLS encryption

3. Access Control
   - Environment-based configuration
   - Secrets management
   - Network policy enforcement
   - Service authentication

## Monitoring and Logging
1. Container Monitoring
   - Health checks
   - Resource usage tracking
   - Container states
   - Service metrics

2. Logging
   - JSON format
   - Log rotation
   - Volume-based storage
   - Structured logging

## Dependencies
1.  **Runtime**
    *   Python packages from `requirements.txt` (FastAPI, OpenAI, python-docx, supabase, etc.)
    *   System libraries needed by Python packages
    *   External service connections (Supabase, potentially other APIs)
    *   Environment variables (`.env` file)

2.  **Infrastructure**
    *   Docker Engine
    *   Docker Swarm
    *   Traefik
    *   Supabase Account and Vector Database

## Known Limitations
1. Resource Constraints
   - Memory limits for document processing
   - CPU allocation
   - Network bandwidth for embedding generation
   - Storage capacity for templates

2. Scaling Considerations
   - Single replica initially
   - Stateless design required
   - Network overhead
   - Resource competition

## Future Improvements
1. Infrastructure
   - Multi-node Swarm setup
   - Advanced monitoring
   - Automated scaling
   - Backup solutions

2. Security
   - Full authentication system
   - Network policies
   - Security scanning
   - Access controls

3. Performance
   - Resource optimization
   - Embedding generation optimization
   - Cache implementation
   - Load balancing improvements