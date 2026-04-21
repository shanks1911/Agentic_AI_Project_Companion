#mongo_memory.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoMemory:

    def __init__(self):

        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["agent_memory"]
        self.sessions = self.db["sessions"]

    def save_session(self, data):

        self.sessions.update_one(
            {
                "project_id": data["project_id"],
                "active": True
            },
            {
                "$set": {
                    "timestamp": data["timestamp"],
                    "summary": data["summary"],
                    "decisions": data["decisions"],
                    "transcript": data["transcript"],
                    "active": True
                },
                "$setOnInsert": {
                    "id": data["id"],
                    "project_id": data["project_id"]
                }
            },
            upsert=True
        )
    def get_sessions(self, project_id):

        return list(

            self.sessions.find(
                {"project_id": project_id}
            ).sort("timestamp", -1)

        )