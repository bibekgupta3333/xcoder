"""
Init Command Implementation

Handles project initialization, configuration setup, and database initialization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from xcoder import get_logger
from xcoder.utils import (confirm_action, display_error, display_info,
                          display_success, display_warning, prompt_input,
                          prompt_select)

logger = get_logger(__name__)


class InitCommand:
    """Initialize XCoder in a project directory."""
    
    XCODER_DIR = ".xcoder"
    CONFIG_FILE = ".xcoderules"
    
    PROJECT_TYPES = {
        "python": {
            "extensions": [".py"],
            "markers": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
            "ignore_patterns": ["__pycache__", "*.pyc", ".venv", "venv", "env"],
        },
        "javascript": {
            "extensions": [".js", ".jsx"],
            "markers": ["package.json", "node_modules"],
            "ignore_patterns": ["node_modules", "dist", "build", ".next"],
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "markers": ["package.json", "tsconfig.json"],
            "ignore_patterns": ["node_modules", "dist", "build", ".next"],
        },
        "go": {
            "extensions": [".go"],
            "markers": ["go.mod", "go.sum"],
            "ignore_patterns": ["vendor", "bin"],
        },
        "rust": {
            "extensions": [".rs"],
            "markers": ["Cargo.toml", "Cargo.lock"],
            "ignore_patterns": ["target"],
        },
        "java": {
            "extensions": [".java"],
            "markers": ["pom.xml", "build.gradle", "settings.gradle"],
            "ignore_patterns": ["target", "build", ".gradle"],
        },
    }
    
    def __init__(self, path: Path, force: bool = False, template: Optional[str] = None):
        """
        Initialize InitCommand.
        
        Args:
            path: Project path to initialize
            force: Force initialization even if already initialized
            template: Configuration template to use
        """
        self.path = path.resolve()
        self.force = force
        self.template = template
        self.xcoder_path = self.path / self.XCODER_DIR
        self.config_path = self.path / self.CONFIG_FILE
        
    def execute(self) -> bool:
        """
        Execute initialization.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already initialized
            if self._is_initialized() and not self.force:
                display_warning(f"XCoder already initialized in {self.path}")
                if not confirm_action("Re-initialize? This will overwrite existing config"):
                    display_info("Initialization cancelled")
                    return False
            
            # Detect project type
            project_type = self._detect_project_type()
            display_info(f"Detected project type: {project_type}")
            
            # Create directory structure
            self._create_directory_structure()
            
            # Generate configuration
            config = self._generate_config(project_type)
            self._save_config(config)
            
            # Initialize databases
            self._initialize_databases()
            
            # Create agent roles config
            self._create_agent_roles()
            
            # Create .gitignore entries
            self._update_gitignore()
            
            display_success(
                "XCoder initialized successfully!",
                details=self._get_init_summary(project_type)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            display_error("Initialization failed", exception=e)
            return False
    
    def _is_initialized(self) -> bool:
        """Check if XCoder is already initialized."""
        return self.xcoder_path.exists() or self.config_path.exists()
    
    def _detect_project_type(self) -> str:
        """
        Detect project type based on files in directory.
        
        Returns:
            Detected project type or 'generic'
        """
        if self.template:
            if self.template in self.PROJECT_TYPES:
                return self.template
            else:
                display_warning(f"Unknown template: {self.template}, auto-detecting...")
        
        # Check for marker files
        for proj_type, config in self.PROJECT_TYPES.items():
            for marker in config["markers"]:
                if (self.path / marker).exists():
                    return proj_type
        
        # Check file extensions
        file_counts: Dict[str, int] = {}
        for proj_type, config in self.PROJECT_TYPES.items():
            count = sum(1 for ext in config["extensions"] for _ in self.path.rglob(f"*{ext}"))
            if count > 0:
                file_counts[proj_type] = count
        
        if file_counts:
            return max(file_counts, key=file_counts.get)
        
        return "generic"
    
    def _create_directory_structure(self):
        """Create .xcoder directory structure."""
        directories = [
            self.xcoder_path,
            self.xcoder_path / "data",
            self.xcoder_path / "cache",
            self.xcoder_path / "logs",
            self.xcoder_path / "memory",
            self.xcoder_path / "agents",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def _generate_config(self, project_type: str) -> Dict[str, Any]:
        """
        Generate configuration based on project type.
        
        Args:
            project_type: Detected project type
            
        Returns:
            Configuration dictionary
        """
        config = {
            "version": "1.0",
            "project": {
                "name": self.path.name,
                "type": project_type,
                "initialized_at": datetime.now().isoformat(),
            },
            "rag": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "nomic-embed-text",
                "vector_db": "chromadb",
            },
            "llm": {
                "default_model": "codellama:7b",
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            "agents": {
                "default_role": "general",
                "roles": [
                    "backend",
                    "frontend",
                    "devops",
                    "testing",
                    "documentation",
                ],
            },
            "ignore_patterns": [
                ".git",
                ".xcoder",
                "node_modules",
                "__pycache__",
                "*.pyc",
                ".venv",
                "venv",
                "dist",
                "build",
            ],
        }
        
        # Add project-specific patterns
        if project_type in self.PROJECT_TYPES:
            proj_config = self.PROJECT_TYPES[project_type]
            config["ignore_patterns"].extend(proj_config["ignore_patterns"])
            config["file_extensions"] = proj_config["extensions"]
        
        return config
    
    def _save_config(self, config: Dict[str, Any]):
        """
        Save configuration to .xcoderules file.
        
        Args:
            config: Configuration dictionary
        """
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {self.config_path}")
    
    def _initialize_databases(self):
        """Initialize vector and memory databases."""
        # Create database metadata files
        db_meta = {
            "vector_db": {
                "type": "chromadb",
                "collection": f"xcoder_{self.path.name}",
                "initialized_at": datetime.now().isoformat(),
            },
            "memory_db": {
                "type": "sqlite",
                "path": str(self.xcoder_path / "memory" / "conversations.db"),
                "initialized_at": datetime.now().isoformat(),
            },
        }
        
        db_meta_path = self.xcoder_path / "data" / "db_metadata.json"
        with open(db_meta_path, "w") as f:
            json.dump(db_meta, f, indent=2)
        
        logger.info("Database metadata initialized")
    
    def _create_agent_roles(self):
        """Create default agent roles configuration."""
        roles_config = {
            "roles": {
                "backend": {
                    "description": "Backend development expert",
                    "expertise": ["API design", "database", "server-side logic"],
                    "tools": ["code_generation", "code_review", "debugging"],
                },
                "frontend": {
                    "description": "Frontend development expert",
                    "expertise": ["UI/UX", "React", "HTML/CSS", "JavaScript"],
                    "tools": ["code_generation", "component_design"],
                },
                "devops": {
                    "description": "DevOps and infrastructure expert",
                    "expertise": ["Docker", "CI/CD", "deployment", "monitoring"],
                    "tools": ["script_generation", "configuration"],
                },
                "testing": {
                    "description": "Testing and quality assurance expert",
                    "expertise": ["unit tests", "integration tests", "test automation"],
                    "tools": ["test_generation", "code_review"],
                },
                "documentation": {
                    "description": "Documentation specialist",
                    "expertise": ["technical writing", "API docs", "tutorials"],
                    "tools": ["doc_generation", "markdown"],
                },
            }
        }
        
        roles_path = self.xcoder_path / "agents" / "roles.yaml"
        with open(roles_path, "w") as f:
            yaml.dump(roles_config, f, default_flow_style=False)
        
        logger.info("Agent roles configuration created")
    
    def _update_gitignore(self):
        """Add .xcoder entries to .gitignore."""
        gitignore_path = self.path / ".gitignore"
        
        entries = [
            "",
            "# XCoder",
            ".xcoder/data/",
            ".xcoder/cache/",
            ".xcoder/logs/",
            ".xcoder/memory/",
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                content = f.read()
            
            if ".xcoder" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n".join(entries) + "\n")
                logger.info("Updated .gitignore")
        else:
            with open(gitignore_path, "w") as f:
                f.write("\n".join(entries) + "\n")
            logger.info("Created .gitignore")
    
    def _get_init_summary(self, project_type: str) -> str:
        """
        Get initialization summary.
        
        Args:
            project_type: Project type
            
        Returns:
            Summary string
        """
        return f"""
Project: {self.path.name}
Type: {project_type}
Location: {self.path}

Created:
  • {self.CONFIG_FILE} - Configuration file
  • {self.XCODER_DIR}/ - Data directory
  • {self.XCODER_DIR}/agents/roles.yaml - Agent roles
  • {self.XCODER_DIR}/data/db_metadata.json - Database metadata

Next steps:
  1. Run 'xcoder ragify' to vectorize your codebase
  2. Run 'xcoder agent -i' to start the interactive agent
  3. Customize {self.CONFIG_FILE} for your needs
"""
"""
