# /src/generate_gantt_plan.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.schemas import GanttPlan
import os
from dotenv import load_dotenv

load_dotenv()


def generate_gantt_plan(project_idea: str) -> GanttPlan:
    """
    Generates a structured Gantt chart plan for a given project idea.
    """
    structured_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_KEY")
    ).with_structured_output(GanttPlan)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert project planner AI. Given a project idea, create a detailed Gantt chart plan.

        Each task must have:
        - A clear, concise task name.
        - Start and end dates that make sense in sequence.
        - Duration in days.
        - Optional dependencies (tasks that must be completed before this one starts).
        - The status must always be "To-Do".

        Ensure the total duration is realistic for a small-to-medium project (e.g., 1–8 weeks).
        Use date strings in "YYYY-MM-DD" format.
        """),
        ("human", "{user_idea}")
    ])

    chain = prompt | structured_llm

    print("📅 Generating structured Gantt chart plan...")
    gantt_plan = chain.invoke({"user_idea": project_idea})
    return gantt_plan
