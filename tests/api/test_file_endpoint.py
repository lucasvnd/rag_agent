import pytest
from unittest.mock import patch, MagicMock
import io

class TestFileEndpoint:
    """Test the /file endpoint for document upload and processing"""

    @patch("app.api.file.get_supabase_client")
    def test_file_upload_pdf(self, mock_get_supabase, test_client, sample_pdf, mock_supabase):
        """Test successful PDF upload to /file endpoint"""
        # Given a mock Supabase client and sample PDF
        mock_get_supabase.return_value = mock_supabase
        
        # When uploading the PDF
        response = test_client.post(
            "/file",
            files={"file": ("sample.pdf", sample_pdf, "application/pdf")}
        )
        
        # Then the response should be successful
        assert response.status_code == 200
        assert "document_id" in response.json()
        
        # And Supabase storage should be called
        mock_supabase.storage.assert_called_once()
    
    @patch("app.api.file.get_supabase_client")
    def test_file_upload_docx(self, mock_get_supabase, test_client, sample_docx, mock_supabase):
        """Test successful DOCX upload to /file endpoint"""
        # Given a mock Supabase client and sample DOCX
        mock_get_supabase.return_value = mock_supabase
        
        # When uploading the DOCX
        response = test_client.post(
            "/file",
            files={"file": ("sample.docx", sample_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        
        # Then the response should be successful
        assert response.status_code == 200
        assert "document_id" in response.json()
    
    @patch("app.api.file.get_supabase_client")
    def test_file_upload_txt(self, mock_get_supabase, test_client, sample_txt, mock_supabase):
        """Test successful TXT upload to /file endpoint"""
        # Given a mock Supabase client and sample TXT
        mock_get_supabase.return_value = mock_supabase
        
        # When uploading the TXT
        response = test_client.post(
            "/file",
            files={"file": ("sample.txt", sample_txt, "text/plain")}
        )
        
        # Then the response should be successful
        assert response.status_code == 200
        assert "document_id" in response.json()
    
    def test_file_upload_unsupported_format(self, test_client):
        """Test upload of unsupported file format"""
        # Given an unsupported file format
        unsupported_file = io.BytesIO(b"This is not a supported file")
        
        # When uploading the file
        response = test_client.post(
            "/file",
            files={"file": ("sample.xyz", unsupported_file, "application/octet-stream")}
        )
        
        # Then the response should indicate an error
        assert response.status_code == 400
        assert "error" in response.json()
        
    def test_file_upload_no_file(self, test_client):
        """Test upload with no file attached"""
        # When making a request with no file
        response = test_client.post("/file")
        
        # Then the response should indicate an error
        assert response.status_code == 422  # FastAPI validation error
    
    @patch("app.api.file.get_supabase_client")
    def test_file_upload_supabase_error(self, mock_get_supabase, test_client, sample_pdf):
        """Test handling of Supabase errors during upload"""
        # Given a Supabase client that raises an exception
        mock_supabase = MagicMock()
        mock_supabase.storage().from_().upload.side_effect = Exception("Supabase error")
        mock_get_supabase.return_value = mock_supabase
        
        # When uploading a file
        response = test_client.post(
            "/file",
            files={"file": ("sample.pdf", sample_pdf, "application/pdf")}
        )
        
        # Then the response should indicate an error
        assert response.status_code == 500
        assert "error" in response.json() 