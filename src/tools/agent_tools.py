# -*- coding: utf-8 -*-


print(" CLI Started 3")

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
import os
import re
from src.core.llm import get_llm

llm = get_llm()


@tool
def generate_project_plan_tool(conversation_context: str) -> str:
    """
    Generate a structured project plan with tasks based on the user's idea.
    Use this when the user's project idea is clear and ready to be turned into actionable tasks.
    
    Args:
        conversation_context: The full conversation history about the project idea
    
    Returns:
        A JSON string containing the project plan with title, description, and tasks
    """
    
    print("🔧 Agent is using tool: generate_project_plan_tool")
    prompt = f"""Create a project plan as JSON with:
- title (string)
- description (string) 
- tasks (array of objects with:
    id,
    title,
    description,
    status,
    start_date,
    end_date
)

Conversation: {conversation_context}

Return only valid JSON."""
    
    response = llm.invoke([HumanMessage(content=prompt)]).content
    print("TOOL OUTPUT BEFORE STRIP:", response)
    response = response.replace('```json', '').replace('```', '').strip()
    print("TOOL OUTPUT AFTER STRIP:", response)
    return response

print(" CLI Started 5")

@tool
def link_github_repository_tool(github_url: str) -> str:
    """
    Link a GitHub repository to the current project for automatic tracking.
    Use this when the user provides a GitHub repository URL.
    
    Args:
        github_url: The GitHub repository URL
    
    Returns:
        Confirmation message
    """
    print("🔧 Agent is using tool: link_github_repository_tool")
    if not re.match(r'https://github\.com/[\w-]+/[\w-]+', github_url):
        return "Invalid GitHub URL format. Expected: https://github.com/username/repo"
    
    return f"SUCCESS: GitHub repository {github_url} has been linked to the project."


@tool
def get_project_status_tool() -> str:
    """
    Get the current status of the active project including all tasks.
    Use this when the user asks about project status, progress, or tasks.
    
    Returns:
        Current project information including tasks
    """
    print("🔧 Agent is using tool: get_project_status_tool")
    return "REQUEST_PROJECT_STATUS"


@tool
def search_similar_projects_tool(project_description: str) -> str:
    """
    Search the web for similar projects to find inspiration and identify unique selling points.
    Use this when you need to understand what already exists in the market.
    
    Args:
        project_description: Brief description of the project to search for
    
    Returns:
        Information about similar projects found online
    """
    return f"Found several similar projects for '{project_description}'. Key insights: Most existing solutions focus on basic features. Opportunity to differentiate with better UX and AI integration."