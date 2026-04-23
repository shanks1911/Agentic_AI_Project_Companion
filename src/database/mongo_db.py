"""
Primary MongoDB persistence layer for project records.

Stores:
- project metadata
- task lists
- timestamps
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class MongoDB:
    """
    Wrapper around MongoDB collections used by the app.
    """
    def __init__(self):
        """Connect to MongoDB and initialize collections."""
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["agent_memory"]

        self.projects = self.db["projects"]

    # ---------------- PROJECTS ----------------
    def save_project(self, project_data):
        """
        Insert or update a project document.

        Args:
            project_data: Dictionary containing project fields.
        """
        project_data["last_modified"] = datetime.now().isoformat()

        self.projects.update_one(
            {"id": project_data["id"]},
            {"$set": project_data},
            upsert=True
        )

    def get_project(self, project_id):
        """
        Fetch a single project by ID.

        Args:
            project_id: Unique project identifier.

        Returns:
            Project document without Mongo _id field.
        """
        return self.projects.find_one(
            {"id": project_id},
            {"_id": 0}
        )

    def list_projects(self):
        """
        Return all projects sorted by last update time.

        Returns:
            List of project summaries.
        """
        data = self.projects.find(
            {},
            {
                "_id": 0,
                "id": 1,
                "title": 1,
                "description": 1,
                "last_modified": 1
            }
        ).sort("last_modified", -1)

        return list(data)

    def save_session(self, session_data):
        """
        Placeholder for compatibility with other storage layers.
        """
        pass

    def get_sessions(self, project_id):
        """
        Placeholder for compatibility with other storage layers.
        """
        return []