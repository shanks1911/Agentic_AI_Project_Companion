#agent_tools.py
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
    prompt = f"""
Create a project plan as valid JSON.

Return:

{{
  "title":"",
  "description":"",
  "sequence_diagram":"plain text sequence diagram",
  "tasks":[
    {{
      "id":1,
      "title":"",
      "description":"",
      "status":"To-Do"
    }}
  ]
}}

RULES:

1. Understand the user's project first.
2. Generate realistic tasks.
3. Generate sequence_diagram as a readable ASCII diagram.

Use columns / lifelines / arrows.

Example:

+------+    +----+    +--------+
|User  |    |UI  |    |Backend |
+------+    +----+    +--------+
   |          |           |
   | Request  |           |
   |--------->|           |
   |          | API Call  |
   |          |---------->|
   |          | Response  |
   |<---------|           |

Do NOT output PlantUML, Mermaid, or script syntax.
Do NOT use loop/end blocks.
Must look visually like a diagram.
4. Use only technologies explicitly mentioned by the user.
5. If technologies are not specified, use generic participants.

Format sequence_diagram like this:

User -> Frontend : Submit Request
Frontend -> Backend : API Call
Backend -> Database : Save Data
Database --> Backend : Success
Backend --> Frontend : Response
Frontend --> User : Show Result

Use multiple participants if needed.

Examples:

For AI system:

User -> UI : Ask question
UI -> Agent : Send prompt
Agent -> Vector DB : Search memory
Vector DB --> Agent : Context
Agent -> LLM : Generate answer
LLM --> Agent : Response
Agent --> UI : Final output
UI --> User : Display result

For ecommerce:

User -> Web App : Place order
Web App -> Payment Service : Process payment
Payment Service --> Web App : Success
Web App -> Database : Save order
Web App --> User : Order confirmed

Keep it readable and practical.

Conversation:
{conversation_context}

Return only valid JSON.
"""
    
    response = llm.invoke([HumanMessage(content=prompt)]).content
    print("TOOL OUTPUT BEFORE STRIP:", response)
    response = response.replace('```json', '').replace('```', '').strip()
    print("TOOL OUTPUT AFTER STRIP:", response)
    return response
