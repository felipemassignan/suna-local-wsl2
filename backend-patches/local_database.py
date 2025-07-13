"""
Local database implementation using SQLite
Substitui o Supabase por uma implementação local
"""

import sqlite3
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
import aiosqlite
from utils.logger import logger
from utils.config import config, is_local_mode


class LocalDatabase:
    """Local SQLite database implementation"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.SQLITE_DB_PATH
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    async def initialize(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Projects table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    user_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Threads table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    user_id TEXT,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    type TEXT,
                    content TEXT,
                    is_llm_message BOOLEAN,
                    created_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads (id)
                )
            """)
            
            # Agent runs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    status TEXT,
                    model_name TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    error_message TEXT,
                    metadata TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads (id)
                )
            """)
            
            # Sessions table (for authentication)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            await db.commit()
            
            # Create default user if not exists
            await self._create_default_user(db)
    
    async def _create_default_user(self, db: aiosqlite.Connection):
        """Create default local user"""
        user_id = config.LOCAL_USER_ID
        
        # Check if user exists
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if await cursor.fetchone():
            return
        
        # Create default user
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO users (id, email, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "local@example.com", now, now, "{}"))
        
        # Create default project
        project_id = config.LOCAL_PROJECT_ID
        await db.execute("""
            INSERT INTO projects (id, name, user_id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, "Projeto Local", user_id, now, now, "{}"))
        
        await db.commit()
        logger.info("Created default local user and project")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
    
    # User operations
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, email: str, user_id: str = None) -> Dict[str, Any]:
        """Create a new user"""
        user_id = user_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO users (id, email, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, email, now, now, "{}"))
            await db.commit()
        
        return await self.get_user(user_id)
    
    # Project operations
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_project(self, name: str, user_id: str, project_id: str = None) -> Dict[str, Any]:
        """Create a new project"""
        project_id = project_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO projects (id, name, user_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, name, user_id, now, now, "{}"))
            await db.commit()
        
        return await self.get_project(project_id)
    
    # Thread operations
    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread by ID"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM threads WHERE id = ?", (thread_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_thread(self, project_id: str, user_id: str, title: str = None, thread_id: str = None) -> Dict[str, Any]:
        """Create a new thread"""
        thread_id = thread_id or str(uuid.uuid4())
        title = title or f"Thread {thread_id[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO threads (id, project_id, user_id, title, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (thread_id, project_id, user_id, title, now, now, "{}"))
            await db.commit()
        
        return await self.get_thread(thread_id)
    
    async def get_user_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all threads for a user"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM threads WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Message operations
    async def add_message(
        self,
        thread_id: str,
        message_type: str,
        content: str,
        is_llm_message: bool = False,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Add a message to a thread"""
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata or {})
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO messages (id, thread_id, type, content, is_llm_message, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message_id, thread_id, message_type, content, is_llm_message, now, metadata_json))
            await db.commit()
        
        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "type": message_type,
            "content": content,
            "is_llm_message": is_llm_message,
            "created_at": now,
            "metadata": metadata or {}
        }
    
    async def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a thread"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at ASC",
                (thread_id,)
            )
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                message = dict(row)
                try:
                    message["metadata"] = json.loads(message["metadata"])
                except:
                    message["metadata"] = {}
                messages.append(message)
            
            return messages
    
    # Agent run operations
    async def create_agent_run(
        self,
        thread_id: str,
        model_name: str = None,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Create a new agent run"""
        run_id = run_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO agent_runs (id, thread_id, status, model_name, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, thread_id, "running", model_name, now, now, "{}"))
            await db.commit()
        
        return {
            "id": run_id,
            "thread_id": thread_id,
            "status": "running",
            "model_name": model_name,
            "created_at": now,
            "updated_at": now
        }
    
    async def update_agent_run_status(
        self,
        run_id: str,
        status: str,
        error_message: str = None
    ):
        """Update agent run status"""
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                UPDATE agent_runs 
                SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status, error_message, now, run_id))
            await db.commit()
    
    # Session operations (for authentication)
    async def create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        access_token = f"local_token_{uuid.uuid4()}"
        refresh_token = f"local_refresh_{uuid.uuid4()}"
        now = datetime.now(timezone.utc).isoformat()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO sessions (id, user_id, access_token, refresh_token, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, access_token, refresh_token, now, now))
            await db.commit()
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": now
        }
    
    async def get_session_by_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get session by access token"""
        async with self.get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE access_token = ?", (access_token,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None


# Global database instance
local_db = LocalDatabase()


class LocalDBConnection:
    """Local database connection wrapper compatible with Supabase interface"""
    
    def __init__(self):
        self.db = local_db
    
    @property
    async def client(self):
        """Get database client (returns self for compatibility)"""
        if not is_local_mode():
            return None
        return self
    
    async def initialize(self):
        """Initialize the database"""
        await self.db.initialize()
    
    # Supabase-compatible methods
    def table(self, table_name: str):
        """Return a table interface"""
        return LocalTableInterface(self.db, table_name)
    
    def from_(self, table_name: str):
        """Alias for table method"""
        return self.table(table_name)


class LocalTableInterface:
    """Local table interface compatible with Supabase table interface"""
    
    def __init__(self, db: LocalDatabase, table_name: str):
        self.db = db
        self.table_name = table_name
        self._select_fields = "*"
        self._where_conditions = []
        self._limit_value = None
        self._order_by_field = None
        self._order_desc = False
    
    def select(self, fields: str = "*"):
        """Select fields"""
        self._select_fields = fields
        return self
    
    def eq(self, field: str, value: Any):
        """Add equality condition"""
        self._where_conditions.append((field, "=", value))
        return self
    
    def limit(self, count: int):
        """Limit results"""
        self._limit_value = count
        return self
    
    def order(self, field: str, desc: bool = False):
        """Order results"""
        self._order_by_field = field
        self._order_desc = desc
        return self
    
    async def execute(self):
        """Execute the query"""
        # This is a simplified implementation
        # In a real implementation, you would build and execute SQL queries
        # based on the accumulated conditions
        
        if self.table_name == "threads":
            if len(self._where_conditions) == 1 and self._where_conditions[0][0] == "user_id":
                user_id = self._where_conditions[0][2]
                threads = await self.db.get_user_threads(user_id)
                return {"data": threads, "error": None}
        
        # Default empty result
        return {"data": [], "error": None}

