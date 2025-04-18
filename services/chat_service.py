from typing import List, Dict, Any, Optional
import os
from openai import OpenAI
from models.schemas import ChatRequest, ChatResponse
from services.vector_store import VectorStore

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_response(query: str, context: List[Dict[str, Any]]) -> str:
    """
    Generate a response using the query and retrieved context
    """
    try:
        # Prepare context string from retrieved chunks
        context_str = "\n\n".join([
            f"Document {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(context)
        ])
        
        # Create the prompt
        prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say so.

Context:
{context_str}

Question: {query}

Answer:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided document context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        raise e

async def query_documents(
    query: str,
    user_id: str,
    context_window: int = 5
) -> ChatResponse:
    """
    Query the document database and return relevant information
    """
    try:
        # Search for relevant chunks in the vector store using text query
        similar_chunks = await VectorStore.search_text(
            query_text=query,
            user_id=user_id,
            limit=context_window
        )
        
        if not similar_chunks:
            return ChatResponse(
                answer="I couldn't find any relevant information in the documents to answer your question.",
                sources=[],
                template_used=None
            )
        
        # Generate response using the retrieved context
        answer = await generate_response(query, similar_chunks)
        
        # Format sources for response
        sources = [
            {
                "content": chunk["content"],
                "document_id": chunk["document_id"],
                "similarity": chunk["similarity"]
            }
            for chunk in similar_chunks
        ]
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            template_used=None
        )
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise e

async def generate_from_template(
    query: str,
    template_id: str,
    user_id: str,
    context_window: int = 5
) -> ChatResponse:
    """
    Generate a response using a template and document context
    """
    try:
        # Search for relevant chunks in the vector store
        similar_chunks = await VectorStore.search_text(
            query_text=query,
            user_id=user_id,
            limit=context_window
        )
        
        if not similar_chunks:
            return ChatResponse(
                answer="I couldn't find any relevant information in the documents to process your template.",
                sources=[],
                template_used=template_id
            )
        
        # Generate a response to extract structured data from the context
        context_str = "\n\n".join([
            f"Document {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(similar_chunks)
        ])
        
        # Create a prompt to extract template variables
        prompt = f"""Based on the following context, extract the information needed for the template. Format your response as a JSON object with the template variables as keys.

Context:
{context_str}

Question/Request: {query}

Extract the relevant information and format it as JSON:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from text. Format your response as a valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse the response as JSON data for template processing
        import json
        try:
            template_data = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the text
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                template_data = json.loads(content[start_idx:end_idx])
            else:
                raise ValueError("Could not extract valid JSON from the response")
        
        # Process the template with the extracted data
        from services.template_processor import TemplateProcessor
        from models.templates import Template
        from uuid import UUID
        
        template_processor = TemplateProcessor()
        
        # Get the template
        # In a real implementation, this would come from a database
        # For now, we'll use the template ID as is
        template = Template(
            id=UUID(template_id),
            name="template",
            file_path=f"templates/modelo_{template_id}.docx",  # Assuming template_id maps to file name
            version=1,
            is_active=True,
            metadata={},
            user_id=UUID(user_id)
        )
        
        # Process the template
        doc = await template_processor.process_template(template, template_data)
        
        # Save the processed template
        from datetime import datetime
        output_filename = f"processed_{template.name}_{datetime.utcnow().timestamp()}.docx"
        output_path = f"templates/{output_filename}"
        await template_processor.save_processed_template(doc, output_path)
        
        # Format sources for response
        sources = [
            {
                "content": chunk["content"],
                "document_id": chunk["document_id"],
                "similarity": chunk["similarity"]
            }
            for chunk in similar_chunks
        ]
        
        return ChatResponse(
            answer=f"I've processed your request and generated a document using the template. You can find it at: {output_path}\n\nThe following information was extracted and used:\n{json.dumps(template_data, indent=2)}",
            sources=sources,
            template_used=template_id
        )
    except Exception as e:
        print(f"Error processing template: {str(e)}")
        return ChatResponse(
            answer=f"An error occurred while processing the template: {str(e)}",
            sources=[],
            template_used=template_id
        ) 