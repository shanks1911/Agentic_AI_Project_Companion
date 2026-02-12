import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class SimpleDB:
    """Ultra-simple database for demo"""
    
    def __init__(self, db_path: str = "demo.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                github_url TEXT,
                data TEXT,
                created_at TEXT,
                last_modified TEXT
            )
        """)
        
        # Sessions table (for memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                timestamp TEXT,
                summary TEXT,
                decisions TEXT,
                transcript TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        self.conn.commit()
    
    def save_project(self, project_data: Dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO projects 
            (id, title, description, github_url, data, created_at, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_data['id'],
            project_data['title'],
            project_data['description'],
            project_data.get('github_url'),
            json.dumps(project_data),
            project_data.get('created_at', datetime.now().isoformat()),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def list_projects(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, description, last_modified FROM projects")
        return [
            {'id': row[0], 'title': row[1], 'description': row[2], 'last_modified': row[3]}
            for row in cursor.fetchall()
        ]
    
    def save_session(self, session_data: Dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions 
            (id, project_id, timestamp, summary, decisions, transcript)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_data['id'],
            session_data['project_id'],
            session_data['timestamp'],
            session_data['summary'],
            json.dumps(session_data.get('decisions', [])),
            json.dumps(session_data.get('transcript', []))
        ))
        self.conn.commit()
    
    def get_sessions(self, project_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, summary, decisions 
            FROM sessions 
            WHERE project_id = ?
            ORDER BY timestamp DESC
        """, (project_id,))
        
        return [
            {
                'id': row[0],
                'timestamp': row[1],
                'summary': row[2],
                'decisions': json.loads(row[3])
            }
            for row in cursor.fetchall()
        ]

# Quick test
if __name__ == "__main__":
    db = SimpleDB()
    test_project = {
        'id': 'test_1',
        'title': 'Test Project',
        'description': 'Testing database',
        'tasks': []
    }
    db.save_project(test_project)
    loaded = db.get_project('test_1')
    print("✅ Database works!" if loaded else "❌ Failed")