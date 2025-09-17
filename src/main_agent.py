import os
import json
from typing import TypedDict, Annotated, Sequence, Optional
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# --- Corrected Imports based on your project structure ---
from src.agents.generate_plan import generate_project_plan
from src.schemas import ProjectPlan, KanbanTask

# --- 1. Agent State (Memory) ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    current_plan: Optional[ProjectPlan] = None

# --- 2. Agent Tools (Abilities) ---
@tool("project-scoping-tool")
def project_scoping_tool(idea: str) -> str:
    """
    Takes an initial idea, generates a structured Kanban plan,
    and returns it as a JSON string for review. Use this first.
    """
    print("\n--- 🛠️ Calling Project Scoping Tool ---")
    plan_object = generate_project_plan(idea)
    return plan_object.model_dump_json(indent=2)

@tool("add_task_to_plan")
def add_task_to_plan(title: str, description: str) -> str:
    """Adds a new task to the current project plan."""
    # This is a placeholder; the actual logic is in the custom_tool_node.
    return f"A new task titled '{title}' will be added to the plan."

@tool("save_project_plan")
def save_project_plan(filename: str) -> str:
    """Saves the final project plan to a JSON file and ends the conversation."""
    # This is a placeholder; the actual logic is in the custom_tool_node.
    return f"The plan will be saved to '{filename}' and the session will end."

tools = [project_scoping_tool, add_task_to_plan, save_project_plan]

# --- 3. The Agent's Core Logic ---
class ConversationalAgent:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY") # Ensure this matches your .env file
        ).bind_tools(tools)

    def agent_node(self, state: AgentState):
        """The main conversational 'brain' of the agent."""
        # The prompt is now simpler and more robust.
        system_prompt = """
        You are an interactive AI project manager. Your workflow is:
        1. Refine an idea with the user, then use 'project_scoping_tool' to create a plan.
        2. Once a plan is created, show it to the user and ask for modifications.
        3. Use the 'add_task_to_plan' tool to add new tasks as requested.
        4. When the user is completely satisfied, use the 'save_project_plan' tool to finish.

        Here is the current project plan:
        {plan}
        """
        # Safely get the plan from the state and format it.
        plan_str = "No plan has been generated yet."
        if state.get("current_plan"):
            plan_str = state["current_plan"].model_dump_json(indent=2)

        messages = [HumanMessage(content=system_prompt.format(plan=plan_str))] + state["messages"]
        
        response = self.model.invoke(messages)
        return {"messages": [response]}

    def custom_tool_node(self, state: AgentState):
        """This node executes tools and directly modifies the agent's state."""
        last_message = state["messages"][-1]
        tool_messages = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name == "project-scoping-tool":
                result_json = project_scoping_tool.invoke(tool_args)
                plan = ProjectPlan.model_validate_json(result_json)
                state['current_plan'] = plan # Directly update the state
                tool_messages.append(ToolMessage(content=f"Successfully generated a plan for '{plan.project_title}'.", tool_call_id=tool_call["id"]))

            elif tool_name == "add_task_to_plan":
                if state.get('current_plan'):
                    new_id = len(state['current_plan'].tasks) + 1
                    new_task = KanbanTask(id=new_id, title=tool_args['title'], description=tool_args['description'])
                    state['current_plan'].tasks.append(new_task)
                    tool_messages.append(ToolMessage(content=f"Successfully added task: '{tool_args['title']}'.", tool_call_id=tool_call["id"]))
                else:
                    tool_messages.append(ToolMessage(content="Error: No plan exists to add a task to.", tool_call_id=tool_call["id"]))

            elif tool_name == "save_project_plan":
                if state.get('current_plan'):
                    filename = tool_args['filename']
                    if not filename.endswith(".json"):
                        filename += ".json"
                    with open(filename, "w") as f:
                        f.write(state['current_plan'].model_dump_json(indent=2))
                    tool_messages.append(ToolMessage(content=f"Plan successfully saved to {filename}.", tool_call_id=tool_call["id"]))
                else:
                    tool_messages.append(ToolMessage(content="Error: No plan to save.", tool_call_id=tool_call["id"]))

        return {"messages": tool_messages}

    def router(self, state: AgentState) -> str:
        """Determines the next step in the workflow."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            # If the save tool was called, we end the process after execution.
            if any(call['name'] == 'save_project_plan' for call in last_message.tool_calls):
                return "call_tool_and_end"
            # Otherwise, we execute the tool and loop back.
            return "call_tool"
        # If no tool is called, the conversation ends for this turn.
        return "END"

# --- 4. The Graph Definition ---
load_dotenv()
workflow = StateGraph(AgentState)
agent = ConversationalAgent()

workflow.add_node("agent_node", agent.agent_node)
workflow.add_node("call_tool_node", agent.custom_tool_node)
workflow.set_entry_point("agent_node")
workflow.add_conditional_edges(
    "agent_node",
    agent.router,
    {"call_tool": "call_tool_node", "call_tool_and_end": "call_tool_node", "END": END}
)
# This edge creates the loop, returning to the agent after a tool is used.
workflow.add_edge("call_tool_node", "agent_node")

app = workflow.compile()

# --- 5. Create the Runner Loop ---
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

        # --- THIS IS THE CORRECTED LOGIC ---
        # Instead of checking for .tool_calls, we check the TYPE of the final message.
        if isinstance(final_message, ToolMessage):
            # If the last message is a ToolMessage, a tool was successfully run.
            print(f"✅ Project Plan Generated:\n{final_message.content}")
        else:
            # Otherwise, it's just a regular chat message from the AI.
            print(f"🤖 AI: {final_message.content}")