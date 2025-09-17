from fastapi import FastAPI
from pydantic import BaseModel

# --- Pydantic Models for Data Validation ---
# These models define the expected structure for our API requests and responses.
# FastAPI uses them to validate incoming data and serialize outgoing data.

class ChatMessage(BaseModel):
    """Defines the structure for a user's chat message."""
    message: str
    # In the future, we can add user_id, session_id, etc.

class ChatResponse(BaseModel):
    """Defines the structure for the AI's response."""
    response: str


# --- FastAPI Application Instance ---
# Create an instance of the FastAPI class
app = FastAPI(
    title="CareerForge API",
    description="The backend API for the CareerForge multi-agent system.",
    version="0.1.0",
)

# --- API Endpoints ---

@app.get("/")
def read_root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to CareerForge AI Co-Pilot"}


@app.get("/health")
def health_check():
    """
    A simple health check endpoint to confirm the server is running.
    """
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_with_agent(user_message: ChatMessage):
    """
    The main endpoint for communicating with the Strategic Career Agent.
    For now, it simply echoes the message back.
    """
    # Placeholder logic: In the future, this will invoke the agent graph.
    ai_response = f"You said: '{user_message.message}'. The agent is not yet connected."

    return ChatResponse(response=ai_response)

