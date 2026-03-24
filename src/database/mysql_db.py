#mysql_db.py
import mysql.connector
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class MySQLDB:

    def __init__(self):

        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB")
        )

        self.create_tables()

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(255) PRIMARY KEY,
            title TEXT,
            description TEXT,
            github_url TEXT,
            data JSON,
            created_at TEXT,
            last_modified TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id VARCHAR(255) PRIMARY KEY,
            project_id VARCHAR(255),
            timestamp TEXT,
            summary TEXT,
            decisions JSON
        )
        """)

        self.conn.commit()

    def save_project(self, project_data: Dict):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO projects
        (id,title,description,github_url,data,created_at,last_modified)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        data=%s,last_modified=%s
        """, (

            project_data["id"],
            project_data["title"],
            project_data["description"],
            project_data.get("github_url"),
            json.dumps(project_data),
            project_data.get("created_at", datetime.now().isoformat()),
            datetime.now().isoformat(),
            json.dumps(project_data),
            datetime.now().isoformat()

        ))

        self.conn.commit()

    def get_project(self, project_id: str) -> Optional[Dict]:

        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM projects WHERE id=%s", (project_id,))
        row = cursor.fetchone()

        return json.loads(row[0]) if row else None

    def list_projects(self) -> List[Dict]:

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT id,title,description,last_modified
        FROM projects
        """)

        return [

            {
                "id": r[0],
                "title": r[1],
                "description": r[2],
                "last_modified": r[3],
            }

            for r in cursor.fetchall()

        ]

    def save_session(self, session_data: Dict):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO sessions
        (id,project_id,timestamp,summary,decisions)
        VALUES (%s,%s,%s,%s,%s)
        """, (

            session_data["id"],
            session_data["project_id"],
            session_data["timestamp"],
            session_data["summary"],
            json.dumps(session_data.get("decisions", []))

        ))

        self.conn.commit()

    def get_sessions(self, project_id: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT id,timestamp,summary,decisions
        FROM sessions
        WHERE project_id=%s
        ORDER BY timestamp DESC
        """, (project_id,))

        return [

            {
                "id": r[0],
                "timestamp": r[1],
                "summary": r[2],
                "decisions": json.loads(r[3]),
            }

            for r in cursor.fetchall()

        ]