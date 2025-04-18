-- Create rag_documents table
CREATE TABLE IF NOT EXISTS rag_documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS rag_documents_embedding_idx 
ON rag_documents 
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
        rag_documents.id,
        rag_documents.content,
        1 - (rag_documents.embedding <=> query_embedding) as similarity,
        rag_documents.metadata
    FROM rag_documents
    WHERE 
        rag_documents.user_id = p_user_id
        AND 1 - (rag_documents.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$; 