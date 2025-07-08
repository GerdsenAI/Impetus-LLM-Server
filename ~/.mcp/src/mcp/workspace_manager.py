"""
Workspace Manager for MCP Tools
Handles workspace detection, identification, and database isolation
"""

import os
import hashlib
import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """Manages workspace detection and isolation for MCP tools"""
    
    def __init__(self):
        self.mcp_base_path = Path.home() / ".mcp"
        self.databases_path = self.mcp_base_path / "databases"
        self.config_path = self.mcp_base_path / "config"
        self.file_storage_path = self.mcp_base_path / "file_storage"
        
        # Ensure directories exist
        for path in [self.mcp_base_path, self.databases_path, self.config_path, self.file_storage_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize workspace properties
        self.root_path = Path.cwd()
        self.git_repo = self._detect_git_repo()
        
        self.workspace_id = self._get_workspace_identifier()
        self.workspace_db_path = self.databases_path / f"workspace_{self.workspace_id}.db"
        self.shared_db_path = self.databases_path / "shared_research.db"
        
        # Initialize databases
        self._init_workspace_database()
        self._init_shared_database()
        
        # Register this workspace
        self._register_workspace()
    
    def _get_workspace_identifier(self) -> str:
        """Generate unique workspace identifier based on multiple factors"""
        factors = []
        current_dir = Path.cwd()
        
        # Factor 1: Git repository info if available
        if GIT_AVAILABLE:
            try:
                repo = git.Repo(current_dir)
                if repo.remotes:
                    factors.append(f"git_remote:{repo.remotes.origin.url}")
                factors.append(f"git_branch:{repo.active_branch.name}")
                logger.debug(f"Git info added to workspace identifier")
            except (git.InvalidGitRepositoryError, git.exc.InvalidGitRepositoryError, AttributeError):
                logger.debug("No valid git repository found")
        
        # Factor 2: VS Code workspace file
        workspace_files = list(current_dir.glob("*.code-workspace"))
        if workspace_files:
            factors.append(f"vscode_workspace:{workspace_files[0].name}")
            logger.debug(f"VS Code workspace file found: {workspace_files[0].name}")
        
        # Factor 3: Project name from directory
        factors.append(f"project_dir:{current_dir.name}")
        
        # Factor 4: Absolute path as fallback
        factors.append(f"abs_path:{current_dir.absolute()}")
        
        # Generate hash
        identifier_string = "|".join(factors)
        workspace_hash = hashlib.sha256(identifier_string.encode()).hexdigest()[:16]
        
        logger.info(f"Workspace identifier generated: {workspace_hash}")
        logger.debug(f"Workspace factors: {factors}")
        
        return workspace_hash
    
    def _init_workspace_database(self):
        """Initialize workspace-specific SQLite database"""
        with sqlite3.connect(self.workspace_db_path) as conn:
            # MCP Memory table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcp_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    data TEXT NOT NULL,
                    priority TEXT DEFAULT 'normal',
                    timestamp REAL NOT NULL,
                    agent TEXT DEFAULT 'claude',
                    UNIQUE(topic, agent)
                )
            ''')
            
            # MCP Context table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcp_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    data TEXT NOT NULL,
                    agent TEXT DEFAULT 'claude',
                    timestamp REAL NOT NULL,
                    shared BOOLEAN DEFAULT 0,
                    UNIQUE(key, agent)
                )
            ''')
            
            # Session History table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcp_session_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    action TEXT NOT NULL,
                    data TEXT,
                    timestamp REAL NOT NULL
                )
            ''')
            
            # Search Cache table (workspace-specific)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcp_search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE,
                    query TEXT NOT NULL,
                    results TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')
            
            conn.commit()
            logger.info(f"Workspace database initialized: {self.workspace_db_path}")
    
    def _init_shared_database(self):
        """Initialize shared research database"""
        with sqlite3.connect(self.shared_db_path) as conn:
            # Shared Research Cache
            conn.execute('''
                CREATE TABLE IF NOT EXISTS research_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE,
                    query TEXT NOT NULL,
                    results TEXT NOT NULL,
                    source TEXT DEFAULT 'brave_search',
                    timestamp REAL NOT NULL
                )
            ''')
            
            # Global Search Index
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_hash TEXT,
                    file_path TEXT,
                    content_hash TEXT,
                    indexed_data TEXT,
                    timestamp REAL NOT NULL,
                    UNIQUE(workspace_hash, file_path)
                )
            ''')
            
            conn.commit()
            logger.info(f"Shared database initialized: {self.shared_db_path}")
    
    def _register_workspace(self):
        """Register this workspace in the global registry"""
        registry_path = self.config_path / "workspace_registry.json"
        
        # Load existing registry
        registry = {}
        if registry_path.exists():
            try:
                with open(registry_path) as f:
                    registry = json.load(f)
            except:
                logger.warning("Could not load workspace registry, creating new one")
        
        # Add this workspace
        workspace_info = {
            "id": self.workspace_id,
            "path": str(Path.cwd().absolute()),
            "name": Path.cwd().name,
            "last_used": time.time(),
            "database_path": str(self.workspace_db_path)
        }
        
        registry[self.workspace_id] = workspace_info
        
        # Save registry
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"Workspace registered: {self.workspace_id}")
    
    def _detect_git_repo(self):
        """Detect if current directory is a git repository"""
        if not GIT_AVAILABLE:
            return None
        
        try:
            return git.Repo(self.root_path)
        except (git.InvalidGitRepositoryError, git.exc.InvalidGitRepositoryError):
            return None
    
    def _detect_project_type(self) -> str:
        """Detect the type of project based on files present"""
        indicators = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile'],
            'javascript': ['package.json', 'yarn.lock', 'package-lock.json'],
            'llm_server': ['gerdsen_ai_server', 'impetus-electron', 'ai.md'],
            'rust': ['Cargo.toml'],
            'go': ['go.mod', 'go.sum'],
            'java': ['pom.xml', 'build.gradle'],
            'csharp': ['*.csproj', '*.sln'],
            'cpp': ['CMakeLists.txt', 'Makefile']
        }
        
        for project_type, files in indicators.items():
            for file_pattern in files:
                if list(self.root_path.glob(file_pattern)):
                    return project_type
        
        return 'unknown'
    
    def _get_workspace_creation_time(self) -> float:
        """Get workspace creation time from database or registry"""
        try:
            registry = self.list_workspaces()
            workspace_info = registry.get(self.workspace_id, {})
            return workspace_info.get('last_used', time.time())
        except:
            return time.time()
    
    def get_workspace_connection(self) -> sqlite3.Connection:
        """Get connection to this workspace's database"""
        return sqlite3.connect(self.workspace_db_path)
    
    def get_shared_connection(self) -> sqlite3.Connection:
        """Get connection to shared research database"""
        return sqlite3.connect(self.shared_db_path)
    
    def remember(self, topic: str, data: str, agent: str = 'claude', priority: str = 'normal') -> bool:
        """Store memory in workspace-specific database"""
        try:
            with self.get_workspace_connection() as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO mcp_memory 
                       (topic, data, agent, timestamp, priority) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (topic, data, agent, time.time(), priority)
                )
                conn.commit()
                logger.debug(f"Memory stored: {topic} for {agent}")
                return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def recall(self, topic: str, agent: str = 'claude') -> Optional[str]:
        """Recall from workspace-specific database"""
        try:
            with self.get_workspace_connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM mcp_memory WHERE topic = ? AND agent = ?",
                    (topic, agent)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error recalling memory: {e}")
            return None
    
    def store_context(self, key: str, data: str, agent: str = 'claude', shared: bool = False) -> bool:
        """Store context in workspace-specific database"""
        try:
            with self.get_workspace_connection() as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO mcp_context 
                       (key, data, agent, timestamp, shared) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (key, data, agent, time.time(), shared)
                )
                conn.commit()
                logger.debug(f"Context stored: {key} for {agent}")
                return True
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False
    
    def retrieve_context(self, key: str, agent: str = 'claude') -> Optional[str]:
        """Retrieve context from workspace-specific database"""
        try:
            with self.get_workspace_connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM mcp_context WHERE key = ? AND agent = ?",
                    (key, agent)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None
    
    def list_workspaces(self) -> Dict[str, Any]:
        """List all registered workspaces"""
        registry_path = self.config_path / "workspace_registry.json"
        
        if not registry_path.exists():
            return {}
        
        try:
            with open(registry_path) as f:
                return json.load(f)
        except:
            return {}
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about the current workspace"""
        return {
            'workspace_id': self.workspace_id,
            'project_type': self._detect_project_type(),
            'root_path': str(self.root_path),
            'git_repository': self.git_repo.working_dir if self.git_repo else None,
            'database_path': str(self.workspace_db_path),
            'created_at': self._get_workspace_creation_time()
        }
    
    def migrate_legacy_data(self, legacy_path: str = ".clinerules") -> bool:
        """Migrate data from legacy .clinerules directory"""
        legacy_path = Path(legacy_path)
        
        if not legacy_path.exists():
            logger.info("No legacy data to migrate")
            return True
        
        try:
            # Migrate context data
            context_path = legacy_path / "mcp_context"
            if context_path.exists():
                for context_file in context_path.glob("*.json"):
                    try:
                        with open(context_file) as f:
                            data = json.load(f)
                        
                        # Extract agent and key from filename
                        filename = context_file.stem
                        if "_" in filename:
                            agent, key = filename.split("_", 1)
                        else:
                            agent, key = "claude", filename
                        
                        self.store_context(key, json.dumps(data.get('data', data)), agent)
                        logger.debug(f"Migrated context: {key}")
                        
                    except Exception as e:
                        logger.warning(f"Could not migrate context file {context_file}: {e}")
            
            # Migrate memory data
            memory_path = legacy_path / "agent_memory"
            if memory_path.exists():
                for memory_file in memory_path.glob("*_memory.json"):
                    try:
                        with open(memory_file) as f:
                            memory_data = json.load(f)
                        
                        agent = memory_file.stem.replace("_memory", "")
                        
                        for topic, item in memory_data.items():
                            data = item.get('data', str(item))
                            priority = item.get('priority', 'normal')
                            self.remember(topic, data, agent, priority)
                            logger.debug(f"Migrated memory: {topic} for {agent}")
                        
                    except Exception as e:
                        logger.warning(f"Could not migrate memory file {memory_file}: {e}")
            
            logger.info("Legacy data migration completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            return False


# Global workspace manager instance
_workspace_manager = None

def get_workspace_manager() -> WorkspaceManager:
    """Get the global workspace manager instance"""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager
