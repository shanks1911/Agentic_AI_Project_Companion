import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.schemas import ProjectPlan, GanttPlan

load_dotenv()


def generate_tasks(project_idea: str, duration: str = "4 weeks") -> ProjectPlan:
    """
    Generate initial tasks for the project for user confirmation.
    Returns a ProjectPlan object with tasks exactly matching ProjectPlan/KanbanTask schema.
    """
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_KEY")
    ).with_structured_output(ProjectPlan)

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
        You are an expert software project manager AI.
        Break down the user's project idea into **5–15 clear, actionable tasks**.
        Each task must strictly follow this format:
        - id (integer, starting from 1)
        - title (short descriptive string)
        - description (brief explanation string)
        - status = "To-Do"

        Do not include Kanban columns or Gantt dates yet.
        Only generate the task list for user confirmation.

        Make sure the JSON keys match the schema exactly.
        The user wants to complete this project in approximately {duration}.
        """),
        ("human", "{idea}")
    ])

    chain = prompt | model
    print(f"🧩 Generating tasks for '{project_idea}' ({duration})...")
    return chain.invoke({"idea": project_idea})


def generate_final_plan(project_idea: str, plan_type: str, duration: str, tasks: ProjectPlan):
    """
    Generate the final Kanban or Gantt plan based on confirmed tasks.
    Returns ProjectPlan or GanttPlan object.
    """
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_KEY")
    )

    plan_type = plan_type.lower().strip()

    if plan_type == "kanban":
        structured_llm = model.with_structured_output(ProjectPlan)
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are an expert software project manager AI.
            Build a **Kanban board** for the project using these confirmed tasks.
            Include all tasks with the following fields exactly:
            - id
            - title
            - description
            - status (To-Do)

            User wants to finish in {duration}.
            Output JSON exactly matching the ProjectPlan schema.
            """),
            ("human", "{tasks}")
        ])
        chain = prompt | structured_llm
        print("🗂️ Generating Kanban plan...")
        return chain.invoke({"tasks": tasks.dict()})

    elif plan_type == "gantt":
        structured_llm = model.with_structured_output(GanttPlan)
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            You are an expert project scheduler AI.
            Generate a **Gantt chart** for the project using these confirmed tasks.
            Each task must include:
            - task_name
            - start_date (YYYY-MM-DD)
            - end_date (YYYY-MM-DD)
            - duration_days (integer)
            - dependencies (list of task_name)
            - status = "To-Do"

            Total project duration should be {duration}.
            Output JSON exactly matching the GanttPlan schema.
            """),
            ("human", "{tasks}")
        ])
        chain = prompt | structured_llm
        print("📅 Generating Gantt plan...")
        return chain.invoke({"tasks": tasks.dict()})

    else:  # both
        kanban = generate_final_plan(project_idea, "kanban", duration, tasks)
        gantt = generate_final_plan(project_idea, "gantt", duration, tasks)
        return {"kanban": kanban, "gantt": gantt}
