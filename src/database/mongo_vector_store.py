#mongo_vector_store.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

load_dotenv()


class MongoVectorMemory:

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["agent_memory"]
        self.collection = self.db["vector_memory"]

        self.embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_KEY")
        )

    def add_memory(self, text, metadata):

        vector = self.embedding.embed_query(text)

        self.collection.update_one(
            {
                "project_id": metadata["project_id"],
                "type": metadata["type"]
            },
            {
                "$set": {
                    "text": text,
                    "embedding": vector,
                    **metadata
                }
            },
            upsert=True
        )

    def search(self, query, project_id=None):

        query_vector = self.embedding.embed_query(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 50,
                    "limit": 8,
                    "filter": {
                        "project_id": project_id
                    } if project_id else {}
                }
            },
            {
                "$project": {
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = self.collection.aggregate(pipeline)

        docs = []

        for r in results:
            docs.append(
                Document(
                    page_content=r["text"],
                    metadata={"score": r["score"]}
                )
            )

        return docs