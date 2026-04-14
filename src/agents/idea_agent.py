from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from src.core.llm import get_llm
import json

llm = get_llm()


class IdeaAgent:
    """
    Handles follow-up discussions, refinement,
    summaries, feature modifications,
    explanations, comparisons.
    """

    def __init__(self):
        self.llm = llm

    def respond(self, user_input: str, project_context: dict) -> str:

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
    global idea_agent_instance

    if idea_agent_instance is None:
        idea_agent_instance = IdeaAgent()

    return idea_agent_instance


@tool
def idea_followup_tool(user_input: str, project_context: str) -> str:
    """
    Handles follow-up conversation related to project idea,
    summaries, refinements, modifications, clarifications.
    """

    agent = get_idea_agent()

    try:
        project_context = json.loads(project_context)
    except:
        project_context = {}

    return agent.respond(user_input, project_context)