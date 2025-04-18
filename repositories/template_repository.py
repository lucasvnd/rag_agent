from typing import List, Optional
from models.templates import Template
import os
import json
from datetime import datetime

class TemplateRepository:
    """
    Repository class for managing document templates
    """
    def __init__(self, templates_dir: str):
        """
        Initialize the template repository
        
        Args:
            templates_dir (str): Directory path where templates are stored
        """
        self.templates_dir = templates_dir
        self.metadata_file = os.path.join(templates_dir, "templates_metadata.json")
        os.makedirs(templates_dir, exist_ok=True)
        
        # Initialize or load metadata
        if not os.path.exists(self.metadata_file):
            self._save_metadata({})
            
    def _load_metadata(self) -> dict:
        """Load templates metadata from JSON file"""
        with open(self.metadata_file, 'r') as f:
            return json.load(f)
            
    def _save_metadata(self, metadata: dict) -> None:
        """Save templates metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
            
    def add_template(self, template: Template) -> None:
        """
        Add a new template to the repository
        
        Args:
            template (Template): Template to add
        """
        metadata = self._load_metadata()
        
        # Store template metadata
        metadata[template.id] = {
            "name": template.name,
            "description": template.description,
            "file_path": template.file_path,
            "variables": template.variables,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
        
        self._save_metadata(metadata)
        
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Retrieve a template by ID
        
        Args:
            template_id (str): ID of the template to retrieve
            
        Returns:
            Optional[Template]: Template if found, None otherwise
        """
        metadata = self._load_metadata()
        if template_id not in metadata:
            return None
            
        template_data = metadata[template_id]
        return Template(
            id=template_id,
            **template_data,
            created_at=datetime.fromisoformat(template_data["created_at"]),
            updated_at=datetime.fromisoformat(template_data["updated_at"])
        )
        
    def list_templates(self) -> List[Template]:
        """
        List all templates in the repository
        
        Returns:
            List[Template]: List of all templates
        """
        metadata = self._load_metadata()
        templates = []
        
        for template_id, template_data in metadata.items():
            templates.append(Template(
                id=template_id,
                **template_data,
                created_at=datetime.fromisoformat(template_data["created_at"]),
                updated_at=datetime.fromisoformat(template_data["updated_at"])
            ))
            
        return templates
        
    def update_template(self, template: Template) -> None:
        """
        Update an existing template
        
        Args:
            template (Template): Template with updated data
        """
        metadata = self._load_metadata()
        if template.id not in metadata:
            raise ValueError(f"Template with ID {template.id} not found")
            
        metadata[template.id] = {
            "name": template.name,
            "description": template.description,
            "file_path": template.file_path,
            "variables": template.variables,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
        
        self._save_metadata(metadata)
        
    def delete_template(self, template_id: str) -> None:
        """
        Delete a template from the repository
        
        Args:
            template_id (str): ID of the template to delete
        """
        metadata = self._load_metadata()
        if template_id not in metadata:
            raise ValueError(f"Template with ID {template_id} not found")
            
        # Delete template file if it exists
        template_path = metadata[template_id]["file_path"]
        if os.path.exists(template_path):
            os.remove(template_path)
            
        # Remove from metadata
        del metadata[template_id]
        self._save_metadata(metadata) 