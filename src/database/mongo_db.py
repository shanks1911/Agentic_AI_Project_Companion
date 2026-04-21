#mongo_db.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class MongoDB:

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["agent_memory"]

        self.projects = self.db["projects"]

    # ---------------- PROJECTS ----------------
    def save_project(self, project_data):

        project_data["last_modified"] = datetime.now().isoformat()

        self.projects.update_one(
            {"id": project_data["id"]},
            {"$set": project_data},
            upsert=True
        )

    def get_project(self, project_id):

        return self.projects.find_one(
            {"id": project_id},
            {"_id": 0}
        )

    def list_projects(self):

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

    # optional if still used somewhere
    def save_session(self, session_data):
        pass

    def get_sessions(self, project_id):
        return []