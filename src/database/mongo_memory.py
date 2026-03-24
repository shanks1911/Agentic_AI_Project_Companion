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

        self.sessions.insert_one(data)

    def get_sessions(self, project_id):

        return list(

            self.sessions.find(
                {"project_id": project_id}
            ).sort("timestamp", -1)

        )