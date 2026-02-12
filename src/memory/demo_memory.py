from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import uuid
from datetime import datetime

class DemoMemory:
    """Minimal memory system for demo"""
    
    def __init__(self, db):
        self.db = db
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY")
        )
    
    def save_session(self, project_id: str, messages: list):
        """Save session with AI-generated summary"""
        
        # Generate summary using LLM
        conversation = "\n".join([
            f"{'User' if i % 2 == 0 else 'AI'}: {msg.content}"
            for i, msg in enumerate(messages)
        ])
        
        summary_prompt = f"""Summarize this conversation in 2-3 sentences, highlighting key decisions:

{conversation}
"""
        
        summary = self.llm.invoke([HumanMessage(content=summary_prompt)]).content
        
        # Extract decisions (simple keyword matching for demo)
        decisions = []
        for msg in messages:
            content_lower = msg.content.lower()
            if any(word in content_lower for word in ['decided', 'choose', 'will use', 'going with']):
                decisions.append(msg.content[:200])
        
        # Save to database
        session_data = {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'decisions': decisions,
            'transcript': [msg.content for msg in messages]
        }
        
        self.db.save_session(session_data)
        return session_data
    
    def load_context(self, project_id: str) -> str:
        """Load recent context for project"""
        sessions = self.db.get_sessions(project_id)
        
        if not sessions:
            return "This is a new project with no previous sessions."
        
        context = "## Previous Sessions:\n\n"
        for session in sessions[:3]:  # Last 3 sessions
            context += f"**{session['timestamp'][:10]}**: {session['summary']}\n\n"
        
        return context