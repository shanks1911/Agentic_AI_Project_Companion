#chroma_store.py
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os


class ChromaMemory:

    def __init__(self):

        self.embedding = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_KEY")
        )

        self.db = Chroma(
            collection_name="agent_memory",
            embedding_function=self.embedding,
            persist_directory="./vector_memory"
        )

    def add_memory(self, text, metadata):

        existing = self.db.similarity_search(text, k=1)

        if existing:
            return

        self.db.add_texts(
            texts=[text],
            metadatas=[metadata]
        )

    def search(self, query, project_id=None):

        if project_id:
            results = self.db.similarity_search_with_score(
                query,
                k=8,
                filter={"project_id": project_id}
            )
        else:
            results = self.db.similarity_search_with_score(query, k=8)

        # Filter + sort
        filtered = []

        for doc, score in results:
            if score < 0.7:  # lower = more similar
                filtered.append((doc, score))

        # Sort by best match
        filtered.sort(key=lambda x: x[1])

        return [doc for doc, _ in filtered]