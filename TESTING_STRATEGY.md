# Testing Strategy

This document outlines our approach to testing core functionalities of the Document Processing System with RAG.

## Test Categories

### 1. Unit Tests

- **Location**: `/tests/unit/`
- **Purpose**: Test individual components in isolation
- **Framework**: pytest

#### Components to Test:

- **Document Processing**
  - Document parsing (PDF, DOCX, TXT)
  - Chunking algorithms
  - Text extraction

- **Embedding Generation**
  - Vector embedding creation
  - Embedding consistency

- **Template Management**
  - Template metadata extraction
  - Template matching algorithms

- **Repository Layer**
  - Supabase client interactions
  - Data retrieval/storage operations

### 2. Integration Tests

- **Location**: `/tests/integration/`
- **Purpose**: Test component interactions
- **Framework**: pytest with appropriate fixtures

#### Flows to Test:

- **Document Upload Flow**
  - File upload → processing → chunking → storage
  - Handling different file types
  - Error cases (invalid files, etc.)

- **RAG Query Flow**
  - Query → embedding → retrieval → response
  - Relevance of retrieved content

- **Template Suggestion Flow**
  - Document analysis → template matching → suggestion

### 3. API Tests

- **Location**: `/tests/api/`
- **Purpose**: Test API endpoints
- **Framework**: pytest with TestClient (FastAPI)

#### Endpoints to Test:

- **`/file` Endpoint**
  - Successful upload scenarios
  - File type validation
  - Error handling

- **`/chat` Endpoint**
  - Query processing
  - Response format validation
  - Error scenarios

### 4. Mock Strategy

- Use pytest fixtures to mock:
  - Supabase responses
  - File operations
  - Embedding generation

## Implementation Plan

1. **Setup Testing Structure**
   ```bash
   git checkout -b feature/testing-infrastructure
   mkdir -p tests/unit tests/integration tests/api tests/fixtures
   touch tests/conftest.py
   ```

2. **Create Base Test Fixtures**
   - Sample documents (PDF, DOCX, TXT)
   - Mock Supabase responses
   - Mock vector embeddings

3. **Implement Unit Tests First**
   ```bash
   git checkout -b feature/unit-tests
   # Create unit tests for document processing
   # Commit changes
   git push origin feature/unit-tests
   ```

4. **Implement Integration Tests**
   ```bash
   git checkout -b feature/integration-tests
   # Create integration tests
   # Commit changes
   git push origin feature/integration-tests
   ```

5. **Implement API Tests**
   ```bash
   git checkout -b feature/api-tests
   # Create API tests 
   # Commit changes
   git push origin feature/api-tests
   ```

## Immediate Testing Tasks

1. **Document Processing Tests**
   - Test PDF parsing with sample documents
   - Test DOCX parsing with sample documents
   - Test chunking strategy with different text lengths

2. **Supabase Integration Tests**
   - Test vector storage with mock embeddings
   - Test retrieval with known vectors

3. **API Endpoint Tests**
   - Test `/file` with sample document uploads
   - Test `/chat` with sample queries

## Continuous Integration

- Add GitHub Actions workflow for automated testing:
  ```yaml
  # .github/workflows/tests.yml
  name: Run Tests
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - name: Install dependencies
          run: |
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            pip install pytest pytest-cov
        - name: Run tests
          run: |
            pytest --cov=./ --cov-report=xml
  ```

## Best Practices

1. **Test-Driven Development**
   - Write tests before implementing features
   - Ensures features meet requirements

2. **Mocking External Services**
   - Don't depend on actual Supabase in unit tests
   - Create realistic mock responses

3. **Test Coverage**
   - Aim for 80%+ coverage of core functionality
   - Use coverage reports to identify gaps

4. **Git Workflow for Tests**
   - Create feature branches for testing features
   - Include tests in feature PRs
   - Never merge features without tests

## Sample Test Cases

### Document Processing Unit Test

```python
def test_pdf_document_parsing():
    # Given a sample PDF
    sample_pdf_path = "tests/fixtures/sample.pdf"
    
    # When parsing the document
    from app.services.document_processor import parse_pdf
    result = parse_pdf(sample_pdf_path)
    
    # Then the text should be extracted correctly
    assert "Expected content" in result.text
    assert len(result.pages) == 5  # Assuming 5 pages
```

### API Test

```python
def test_file_upload_endpoint(test_client, sample_pdf):
    # Given a test client and sample PDF
    
    # When uploading the file
    response = test_client.post(
        "/file",
        files={"file": ("sample.pdf", sample_pdf, "application/pdf")}
    )
    
    # Then the response should be successful
    assert response.status_code == 200
    assert "document_id" in response.json()
```

By following this strategy, we can ensure our application works correctly while maintaining the quality standards established in our Git workflow. 