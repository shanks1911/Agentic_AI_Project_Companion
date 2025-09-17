import os
import json
from typing import TypedDict, Annotated, Sequence, Optional
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Make sure these imports match your file structure
from src.agents.generate_plan import generate_project_plan
from src.schemas import ProjectPlan

# --- Agent's Memory (State) ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    # This key will hold the plan after generation
    final_plan: Optional[str] = None

# --- Agent's Tools ---
@tool("project-scoping-tool")
def project_scoping_tool(idea: str) -> str:
    """
    Takes a user's refined project idea, generates a structured Kanban plan,
    and returns it as a JSON string for review.
    """
    print("\n--- 🛠️ Calling Project Scoping Tool ---")
    plan_object = generate_project_plan(idea)
    return plan_object.model_dump_json(indent=2)

@tool("save_project_plan")
def save_project_plan(filename: str, plan_json: str) -> str:
    """
    Saves the provided project plan JSON string to a file and ends the session.
    Args:
        filename: The name for the JSON file (e.g., 'my_project_plan').
        plan_json: The complete project plan as a JSON string.
    """
    print(f"\n--- 💾 Saving plan to {filename} ---")
    try:
        if not filename.endswith(".json"):
            filename += ".json"
        
        with open(filename, "w") as f:
            f.write(plan_json)
        return f"Plan successfully saved to {filename}."
    except Exception as e:
        return f"Error saving file: {e}"

tools = [project_scoping_tool, save_project_plan]

# --- Upgraded Agent Logic ---
class ConversationalAgent:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GEMINI_KEY") # Use your .env key name
        ).bind_tools(tools)

    def agent_node(self, state: AgentState):
        """The main conversational 'brain' of the agent."""
        # --- NEW: Upgraded System Prompt ---
        system_prompt = """
        You are a helpful AI project assistant. Your workflow is a two-step process:
        1.  First, have a conversation with the user to refine their project idea. Once the idea is clear, you MUST call the 'project_scoping_tool' to generate a plan.
        2.  After the plan is generated and the result is shown to the user, YOUR NEXT JOB is to ask the user if they want to save it. If they say yes, you MUST call the 'save_project_plan' tool. To do this, you need two arguments:
            - 'filename': A suitable filename for the project.
            - 'plan_json': THIS IS CRITICAL. You must get this value from the content of the preceding ToolMessage in the conversation history.
        """
        messages = [HumanMessage(content=system_prompt)] + state["messages"]
        response = self.model.invoke(messages)
        return {"messages": [response]}

    def router(self, state: AgentState) -> str:
        """Determines the next step based on the agent's last message."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            # If the save tool is called, we will end the graph after.
            if any(call['name'] == 'save_project_plan' for call in last_message.tool_calls):
                return "call_tool_and_end"
            # For any other tool (like scoping), we call it and loop back.
            return "call_tool_and_continue"
        else:
            # If the AI is just chatting, let the user respond.
            return "continue_chat"

# --- Build and Compile the NEW Graph ---
load_dotenv()
workflow = StateGraph(AgentState)
agent = ConversationalAgent()

# The ToolNode now knows about ALL our tools
tool_node = ToolNode(tools)

workflow.add_node("agent_node", agent.agent_node)
workflow.add_node("tool_node", tool_node)

workflow.set_entry_point("agent_node")

workflow.add_conditional_edges(
    "agent_node",
    agent.router,
    {
        "call_tool_and_continue": "tool_node",
        "call_tool_and_end": "tool_node",
        "continue_chat": END # End the turn to wait for user input
    }
)

# --- THIS IS THE NEW LOOP ---
# After the tool node runs, if it wasn't the "end" path, it goes back to the agent.
workflow.add_edge("tool_node", "agent_node")

app = workflow.compile()

# --- Runner Loop ---
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
        
        result_state = app.invoke({"messages": conversation_history})
        
        final_message = result_state['messages'][-1]
        conversation_history.append(final_message)

        if isinstance(final_message, ToolMessage):
            print(f"✅ Tool Result:\n{final_message.content}")
            # If the save tool was successful, we can exit the loop.
            if "successfully saved" in final_message.content.lower():
                print("🎉 Session complete. Goodbye!")
                break
        else:
            print(f"🤖 AI: {final_message.content}")

