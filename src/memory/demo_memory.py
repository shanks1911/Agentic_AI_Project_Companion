
from langchain_core.messages import HumanMessage
import os
import uuid
from datetime import datetime

from src.database.mongo_memory import MongoMemory
from src.database.chroma_store import ChromaMemory
from src.core.llm import get_llm


llm = get_llm()


class DemoMemory:
    """
    Memory manager for the agent.

    Responsibilities:
    MongoDB  → store full conversation sessions
    ChromaDB → store semantic summaries for retrieval
    """

    def __init__(self, db):
        self.db = db  

        # Conversation memory
        self.mongo = MongoMemory()

        # Vector memory
        self.vector = ChromaMemory()

        # LLM for summarization
        self.llm = llm

    def save_session(self, project_id: str, messages: list):
        """
        Save session memory after a conversation ends
        """

        # Build conversation string
        conversation = "\n".join([
            f"{'User' if i % 2 == 0 else 'AI'}: {msg.content}"
            for i, msg in enumerate(messages)
        ])

        # Generate summary
        summary_prompt = f"""
        Summarize this conversation.

        Preserve important information:

        - project idea
        - chosen tech stack
        - decisions made
        - new features added
        - modifications to project plan

        Conversation:
        {conversation}
        """

        summary = self.llm.invoke(
            [HumanMessage(content=summary_prompt)]
        ).content

        # Extract decisions (simple heuristic)
        decisions = []
        for msg in messages:
            content_lower = msg.content.lower()

            if any(word in content_lower for word in [
                "decided",
                "choose",
                "will use",
                "going with"
            ]):
                decisions.append(msg.content[:200])

        # Build session object
        session_data = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "decisions": decisions,
            "transcript": [msg.content for msg in messages]
        }

        # Store conversation in MongoDB
        self.mongo.save_session(session_data)

        # ✅ ALSO STORE IN MYSQL
        self.db.save_session(session_data)

        # Store summary embedding in ChromaDB
        self.vector.add_memory(
            summary,
            {
                "project_id": project_id,
                "timestamp": session_data["timestamp"],
                "type": "session_summary",
                "source": "conversation",
                "importance": len(decisions)  # heuristic
            }
        )

        return session_data

    def retrieve_semantic_memory(self, query: str, project_id: str) -> str:
        """
        Retrieve relevant past memory using vector search
        """

        try:
            results = self.vector.search(query, project_id)

            context = ""

            for r in results:
                context += r.page_content + "\n"

            return context

        except:
            return ""

    def load_context(self, project_id: str) -> str:
        """
        Load recent memory context for the project
        """

        sessions = self.mongo.get_sessions(project_id)

        if not sessions:
            return "This is a new project with no previous sessions."

        context = "## Previous Sessions:\n\n"

        for session in sessions[:3]:  # last 3 sessions
            context += (
                f"**{session['timestamp'][:10]}**: "
                f"{session['summary']}\n\n"
            )

        return context
    
    def get_recent_transcript(self, project_id: str, limit: int = 1) -> str:
        """
        Get recent raw conversations for better context
        """

        sessions = self.mongo.get_sessions(project_id)

        if not sessions:
            return ""

        context = "## Recent Conversation:\n\n"

        for session in sessions[:limit]:
            transcript = session.get("transcript", [])

            for line in transcript[-6:]:  # last few messages
                context += f"{line}\n"

        return context