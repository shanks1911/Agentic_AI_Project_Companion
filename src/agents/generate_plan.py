from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.schemas import ProjectPlan
import os

from dotenv import load_dotenv
load_dotenv()

def generate_project_plan(finalized_idea: str) -> ProjectPlan:
    """
    This is the core agent logic. It takes a user's idea and returns a structured Pydantic ProjectPlan object.
    """

    structured_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GEMINI_KEY")).with_structured_output(ProjectPlan)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert project manager AI. Your job is to take a user's idea
        and create a clear, structured project plan with multiple initial tasks
        that can be used on a Kanban board. These can be 5-15 or even more steps if needed accordingly.

        IMPORTANT: For every task you create, the 'status' field MUST be
        the exact string 'To-Do'.
        """),
        ("human", "{user_idea}")
    ])
    
    # Langchain chain. will check the prompt and then pipe it to structured llm
    chain = prompt | structured_llm
    
    print("🤖 Thinking and generating your project plan...")
    
    project_plan = chain.invoke({"user_idea": finalized_idea})
    return project_plan