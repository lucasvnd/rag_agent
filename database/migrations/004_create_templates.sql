-- Create templates table
create table templates (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid not null,  -- Reference to the user who owns the template
    name text not null,     -- Template name (e.g., 'modelo_a')
    description text,       -- Template description
    file_path text not null, -- Path to the template file
    metadata jsonb default '{}'::jsonb,  -- Additional template metadata (required fields, etc.)
    version int default 1,   -- Template version
    is_active boolean default true,  -- Whether the template is active
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create index for better performance
create index idx_templates_user_id on templates(user_id);
create index idx_templates_name on templates(name);
create index idx_templates_metadata on templates using gin (metadata);

-- Enable Row Level Security (RLS)
alter table templates enable row level security;

-- Create policies for templates
create policy "Users can insert their own templates"
    on templates for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy "Users can view their own templates"
    on templates for select
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can update their own templates"
    on templates for update
    to authenticated
    using (auth.uid() = user_id);

create policy "Users can delete their own templates"
    on templates for delete
    to authenticated
    using (auth.uid() = user_id);

-- Create function to update template version
create function update_template_version(
    template_id uuid
) returns void
language plpgsql
as $$
begin
    update templates
    set 
        version = version + 1,
        updated_at = timezone('utc'::text, now())
    where id = template_id;
end;
$$;

-- Create function to get active templates for user
create function get_active_templates(
    user_uuid uuid
) returns table (
    id uuid,
    name text,
    description text,
    metadata jsonb,
    version int
)
language plpgsql
as $$
begin
    return query
    select
        templates.id,
        templates.name,
        templates.description,
        templates.metadata,
        templates.version
    from templates
    where
        templates.user_id = user_uuid
        and templates.is_active = true
    order by templates.name;
end;
$$; 