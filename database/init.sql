-- Enable the pgvector extension for vector similarity search
create extension if not exists vector;

-- Create the documents table to store document metadata
create table documents (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid not null,  -- Reference to the user who uploaded the document
    filename text not null,
    file_type text not null,  -- 'pdf' or 'docx'
    status text not null,     -- 'processing', 'completed', 'error'
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    error_message text
);

-- Create the document chunks table with vector embeddings
create table chunks (
    id uuid default uuid_generate_v4() primary key,
    document_id uuid references documents(id) on delete cascade,
    user_id uuid not null,  -- Reference to the user for direct querying
    content text not null,
    embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Add indexes for better query performance
    constraint fk_document foreign key (document_id) references documents(id) on delete cascade
);

-- Create indexes for better performance
create index idx_chunks_user_id on chunks(user_id);
create index idx_documents_user_id on documents(user_id);
create index idx_chunks_embedding on chunks using ivfflat (embedding vector_cosine_ops);
create index idx_chunks_metadata on chunks using gin (metadata);
create index idx_documents_metadata on documents using gin (metadata);

-- Create a function to search for chunks by user
create function match_chunks (
    query_embedding vector(1536),
    user_id uuid,
    match_count int default 5,
    similarity_threshold float default 0.7,
    filter jsonb default '{}'::jsonb
) returns table (
    id uuid,
    content text,
    document_id uuid,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        chunks.id,
        chunks.content,
        chunks.document_id,
        chunks.metadata,
        1 - (chunks.embedding <=> query_embedding) as similarity
    from chunks
    where
        chunks.user_id = user_id
        and chunks.metadata @> filter
        and (1 - (chunks.embedding <=> query_embedding)) > similarity_threshold
    order by chunks.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- Create a function to update document status
create function update_document_status(
    doc_id uuid,
    new_status text,
    error_msg text default null
) returns void
language plpgsql
as $$
begin
    update documents
    set 
        status = new_status,
        error_message = error_msg,
        updated_at = timezone('utc'::text, now())
    where id = doc_id;
end;
$$;

-- Enable Row Level Security (RLS)
alter table documents enable row level security;
alter table chunks enable row level security;

-- Create policies for documents
create policy "Users can insert their own documents"
    on documents for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy "Users can view their own documents"
    on documents for select
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can update their own documents"
    on documents for update
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can delete their own documents"
    on documents for delete
    to authenticated
    using (auth.uid() = user_id);

-- Create policies for chunks
create policy "Users can insert their own chunks"
    on chunks for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy "Users can view their own chunks"
    on chunks for select
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can update their own chunks"
    on chunks for update
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can delete their own chunks"
    on chunks for delete
    to authenticated
    using (auth.uid() = user_id); 