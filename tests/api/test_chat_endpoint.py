import pytest
from unittest.mock import patch, MagicMock
import json

class TestChatEndpoint:
    """Test the /chat endpoint for document interaction"""

    @patch("app.api.chat.get_supabase_client")
    @patch("app.api.chat.get_embedding")
    def test_chat_query(self, mock_get_embedding, mock_get_supabase, test_client, mock_supabase, sample_embedding):
        """Test successful query to chat endpoint"""
        # Given a mock Supabase client and embedding
        mock_get_supabase.return_value = mock_supabase
        mock_get_embedding.return_value = sample_embedding
        
        # Configure mock Supabase to return document chunks
        mock_supabase.rpc().execute.return_value = {
            "data": [
                {
                    "id": "chunk1",
                    "document_id": "doc1",
                    "content": "This is chunk 1 content",
                    "metadata": json.dumps({"page": 1})
                },
                {
                    "id": "chunk2",
                    "document_id": "doc1",
                    "content": "This is chunk 2 content",
                    "metadata": json.dumps({"page": 2})
                }
            ]
        }
        
        # When sending a chat query
        response = test_client.post(
            "/chat",
            json={"query": "What does the document say about templates?", "document_id": "doc1"}
        )
        
        # Then the response should be successful
        assert response.status_code == 200
        assert "answer" in response.json()
        assert "source_chunks" in response.json()
        assert len(response.json()["source_chunks"]) == 2
    
    def test_chat_empty_query(self, test_client):
        """Test handling of empty queries"""
        # When sending an empty query
        response = test_client.post(
            "/chat",
            json={"query": "", "document_id": "doc1"}
        )
        
        # Then the response should indicate an error
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_chat_missing_document_id(self, test_client):
        """Test handling of missing document ID"""
        # When sending a query without document_id
        response = test_client.post(
            "/chat",
            json={"query": "What is this document about?"}
        )
        
        # Then the response should indicate an error
        assert response.status_code == 422  # FastAPI validation error
    
    @patch("app.api.chat.get_supabase_client")
    @patch("app.api.chat.get_embedding")
    def test_chat_no_results(self, mock_get_embedding, mock_get_supabase, test_client, mock_supabase, sample_embedding):
        """Test handling when no relevant chunks are found"""
        # Given a mock Supabase client that returns no results
        mock_get_supabase.return_value = mock_supabase
        mock_get_embedding.return_value = sample_embedding
        mock_supabase.rpc().execute.return_value = {"data": []}
        
        # When sending a chat query
        response = test_client.post(
            "/chat",
            json={"query": "What does the document say about templates?", "document_id": "doc1"}
        )
        
        # Then the response should indicate no results found
        assert response.status_code == 200
        assert "answer" in response.json()
        assert "No relevant information found" in response.json()["answer"]
    
    @patch("app.api.chat.get_supabase_client")
    @patch("app.api.chat.get_embedding")
    def test_chat_suggested_templates(self, mock_get_embedding, mock_get_supabase, test_client, mock_supabase, sample_embedding):
        """Test template suggestions in chat response"""
        # Given a mock Supabase client and embedding
        mock_get_supabase.return_value = mock_supabase
        mock_get_embedding.return_value = sample_embedding
        
        # Configure mock to return document chunks
        mock_supabase.rpc().execute.return_value = {
            "data": [
                {
                    "id": "chunk1",
                    "document_id": "doc1",
                    "content": "This document is about legal contracts",
                    "metadata": json.dumps({"page": 1})
                }
            ]
        }
        
        # And mock to return template suggestions
        mock_supabase.table().select().execute.return_value = {
            "data": [
                {
                    "id": "template1",
                    "name": "Legal Contract Template",
                    "description": "Standard legal contract",
                    "path": "/templates/legal_contract.docx"
                },
                {
                    "id": "template2",
                    "name": "NDA Template",
                    "description": "Non-disclosure agreement",
                    "path": "/templates/nda.docx"
                }
            ]
        }
        
        # When sending a chat query for template suggestions
        response = test_client.post(
            "/chat",
            json={"query": "Suggest templates for this document", "document_id": "doc1"}
        )
        
        # Then the response should include template suggestions
        assert response.status_code == 200
        assert "suggested_templates" in response.json()
        assert len(response.json()["suggested_templates"]) == 2 