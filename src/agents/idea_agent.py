"""
Idea follow-up agent for post-creation project discussions.

This module is responsible for handling conversational requests after a
project idea already exists. It is intentionally focused on natural
language guidance rather than structured plan generation.

Typical use cases:
- Summarize the current project
- Refine or improve an existing idea
- Add / remove / modify features
- Compare technologies or implementation options
- Explain next steps
- Answer follow-up clarification questions
"""
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from src.core.llm import get_llm
import json

llm = get_llm()


class IdeaAgent:
    """
    Lightweight conversational agent for project refinement.

    Uses the shared LLM instance and current project context to generate
    practical product or technical guidance based on user follow-up input.
    """
    def __init__(self):
        """Initialize the agent with the shared LLM instance."""
        self.llm = llm

    def respond(self, user_input: str, project_context: dict) -> str:
        """
        Generate a context-aware response for a follow-up request.

        Args:
            user_input: Latest user query or request.
            project_context: Existing project data used for grounding.

        Returns:
            Natural language assistant response.
        """        

        prompt = f"""
You are an expert AI startup/product strategist.

Current Project:
{json.dumps(project_context, indent=2)}

User Request:
{user_input}

Your job:

- If user asks summary → summarize clearly
- If asks refine idea → improve it
- If asks add/change/remove features → update idea intelligently
- If asks compare tech stacks/options → compare with pros/cons
- If asks explain tasks/research → explain simply
- If asks clarification → answer naturally
- If asks next steps → provide guidance

Rules:
- Be practical
- Be concise
- Be helpful
- Do NOT generate task JSON
- Do NOT generate literature review unless explicitly asked

Give best response.
"""

        return self.llm.invoke(
            [HumanMessage(content=prompt)]
        ).content


# Lazy loader
idea_agent_instance = None


def get_idea_agent():
    """
    Return a shared IdeaAgent instance.

    Creates the instance only once and reuses it across calls to reduce
    initialization overhead.

    Returns:
        IdeaAgent
    """
    global idea_agent_instance

    if idea_agent_instance is None:
        idea_agent_instance = IdeaAgent()

    return idea_agent_instance


@tool
def idea_followup_tool(user_input: str, project_context: str) -> str:
    """
    Tool wrapper for the IdeaAgent.

    Accepts serialized project context, safely converts it into a Python
    dictionary, and returns a conversational response.

    Args:
        user_input: Latest user request.
        project_context: JSON string representing current project state.

    Returns:
        Assistant response string.
    """
    agent = get_idea_agent()

    try:
        project_context = json.loads(project_context)
    except:
        project_context = {}

    return agent.respond(user_input, project_context)