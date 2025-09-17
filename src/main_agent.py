import os
from typing import TypedDict, Annotated, Sequence, Optional
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agents.generate_plan import generate_project_plan
from src.schemas import ProjectPlan

# --- Agent's Memory (State) ---

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    final_plan: Optional[ProjectPlan] = None

# --- Agent's Tools ---
@tool("project-scoping-tool")
def project_scoping_tool(idea: str) -> str:
    """
    Takes a user's final, refined project idea, generates a structured 
    Kanban plan, and returns it as a JSON string for review.
    """
    print("\n--- 🛠️ Calling Project Scoping Tool ---")
    plan_object = generate_project_plan(idea)
    # The tool returns the plan as a nicely formatted JSON string
    return plan_object.model_dump_json(indent=2)

class ConversationalAgent:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY")
        ).bind_tools([project_scoping_tool])

    def refinement_node(self, state: AgentState):
        """Chats with the user to refine their project idea."""
        system_prompt = """
        You are a helpful AI project assistant. Your goal is to have a conversation 
        with the user to refine their project idea. Ask clarifying questions to understand 
        the core features and goals.

        Once the user is happy with the idea and says something like 
        'that's perfect, generate the plan' or 'create the project plan', 
        call the 'project_scoping_tool' with the final, summarized idea.
        """
        messages = [HumanMessage(content=system_prompt)] + state["messages"]
        response = self.model.invoke(messages)
        return {"messages": [response]}

    def router(self, state: AgentState) -> str:
        """Determines the next step based on the agent's last message."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "call_tool"
        else:
            return "END"

# --- Build and Compile the Graph ---
load_dotenv()
workflow = StateGraph(AgentState)
agent = ConversationalAgent()

workflow.add_node("refinement_node", agent.refinement_node)
workflow.add_node("call_tool", ToolNode([project_scoping_tool]))
workflow.set_entry_point("refinement_node")
workflow.add_conditional_edges(
    "refinement_node",
    agent.router,
    {"call_tool": "call_tool", "END": END}
)
workflow.add_edge("call_tool", END)
app = workflow.compile()

if __name__ == "__main__":
    print("🤖 Hello! I'm your Project Scoping Assistant. Let's define your idea.")
    print("   Type 'exit' to end the conversation.")
    
    conversation_history = []

    while True:
        user_input = input("👤 You: ")
        if user_input.lower() == 'exit':
            print("👋 Goodbye!")
            break

        conversation_history.append(HumanMessage(content=user_input))
        result = app.invoke({"messages": conversation_history})
        final_message = result['messages'][-1]
        conversation_history.append(final_message)

        if isinstance(final_message, ToolMessage):
            # If the last message is a ToolMessage, a tool was successfully run.
            print(f"✅ Project Plan Generated:\n{final_message.content}")
        else:
            # Otherwise, it's just a regular chat message from the AI.
            print(f"🤖 AI: {final_message.content}")

