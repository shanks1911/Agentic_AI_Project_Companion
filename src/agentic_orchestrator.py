# -*- coding: utf-8 -*-


"""
True agentic orchestrator using LangGraph
Agent autonomously decides which tools to use
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
import os
import json
import uuid
from datetime import datetime


from src.database.simple_db import SimpleDB
from src.memory.demo_memory import DemoMemory

print(" CLI Started 2")
from src.tools.agent_tools import generate_project_plan_tool

from src.tools.agent_tools import link_github_repository_tool
from src.tools.agent_tools import get_project_status_tool
from src.tools.agent_tools import search_similar_projects_tool
from src.tools.github_analyzer import (
    analyze_github_code_comprehensively_tool,
    match_code_to_tasks_semantic_tool
)
from src.agents.research_agent import search_research_papers_tool, generate_literature_review_tool

tools = [
    generate_project_plan_tool,
    link_github_repository_tool,
    get_project_status_tool,
    search_similar_projects_tool,
    analyze_github_code_comprehensively_tool,  # NEW
    match_code_to_tasks_semantic_tool,         # NEW
    search_research_papers_tool,
    generate_literature_review_tool
]
# Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    project_id: str
    current_project: dict


class AgenticOrchestrator:
    """
    Agentic orchestrator where the agent decides what to do
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY"),
            temperature=0.3
        )
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.db = SimpleDB()
        self.memory = DemoMemory(self.db)
        self.current_project_id = None
        self.current_project = None
        self.messages_history = []
        
        # Build the graph
        self.app = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # After tools, go back to agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """
        Agent node - decides what to do next
        """
        system_prompt = """You are an intelligent AI project assistant. Your role is to help users plan and manage their software projects.

    You have access to these tools:
    1. generate_project_plan_tool - Create a structured project plan with tasks
    2. link_github_repository_tool - Connect a GitHub repository to the project
    3. get_project_status_tool - Get current project information
    4. search_similar_projects_tool - Find similar projects for inspiration
    5. analyze_github_code_comprehensively_tool - Analyze entire GitHub repo by reading ALL code files
    6. match_code_to_tasks_semantic_tool - Semantically match code to tasks and auto-update statuses
    7. search_research_papers_tool - Search academic papers from ArXiv and Semantic Scholar
    8. generate_literature_review_tool - Generate literature review with citations

    Your workflow:
    1. First, help the user REFINE their project idea by asking clarifying questions
    2. Once the idea is clear, use generate_project_plan_tool to create the plan
    3. If the user provides a GitHub URL, use link_github_repository_tool
    4. To analyze what's actually coded, use analyze_github_code_comprehensively_tool
    5. To update task statuses based on real code, use match_code_to_tasks_semantic_tool with just the GitHub URL
    6. If user asks for research papers, use search_research_papers_tool
    7. If user wants a literature review, use generate_literature_review_tool
    8. If the user asks about status/progress, use get_project_status_tool

    IMPORTANT: 
    - match_code_to_tasks_semantic_tool uses pure NLP - no task IDs needed
    - It reads ALL code files and matches semantically to task descriptions
    - Only pass github_url parameter

    Be conversational and helpful. Don't use tools until you have enough information.
    """
        
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    def _tool_node(self, state: AgentState) -> AgentState:
        """
        Execute tools that the agent decided to use
        """
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            print(f"\n🔧 Agent is using tool: {tool_name}")
            print(f"   Arguments: {tool_args}")
            
            # Execute the appropriate tool
            if tool_name == "generate_project_plan_tool":
                result = generate_project_plan_tool.invoke(tool_args)
                
                # Parse and save to database
                try:
                    plan_data = json.loads(result)
                    project_data = {
                        'id': state["project_id"],
                        'title': plan_data.get('title', 'Untitled Project'),
                        'description': plan_data.get('description', ''),
                        'tasks': plan_data.get('tasks', []),
                        'github_url': None,
                        'created_at': datetime.now().isoformat()
                    }
                    self.db.save_project(project_data)
                    self.current_project = project_data
                    
                    result = f"✅ Project plan created successfully!\n\nTitle: {project_data['title']}\nDescription: {project_data['description']}\nTasks: {len(project_data['tasks'])} tasks created"
                except json.JSONDecodeError:
                    result = "Plan generated but couldn't parse. Please try again."
            
            elif tool_name == "link_github_repository_tool":
                result = link_github_repository_tool.invoke(tool_args)
                
                if "SUCCESS" in result:
                    github_url = tool_args.get("github_url")
                    if self.current_project:
                        self.current_project['github_url'] = github_url
                        self.db.save_project(self.current_project)
            
            elif tool_name == "get_project_status_tool":
                if self.current_project:
                    project = self.current_project
                    result = f"📊 Project: {project['title']}\n"
                    result += f"Description: {project['description']}\n\n"
                    result += f"Tasks ({len(project.get('tasks', []))}):\n"
                    for task in project.get('tasks', [])[:5]:
                        result += f"• [{task['status']}] {task['title']}\n"
                else:
                    result = "No active project. Start by describing your project idea."
            
            elif tool_name == "search_similar_projects_tool":
                result = search_similar_projects_tool.invoke(tool_args)

            elif tool_name == "analyze_github_code_comprehensively_tool":
                result = analyze_github_code_comprehensively_tool.invoke(tool_args)

            elif tool_name == "match_code_to_tasks_semantic_tool" or tool_name == "match_code_to_tasks_tool":
                # Semantic matching - no JSON, no task IDs needed
                github_url = tool_args.get("github_url")
                
                if not self.current_project:
                    result = "No active project found."
                elif not github_url:
                    result = "GitHub URL required"
                else:
                    tasks = self.current_project.get('tasks', [])
                    
                    if not tasks:
                        result = "No tasks in project"
                    else:
                        from src.tools.github_analyzer import get_analyzer
                        
                        try:
                            a = get_analyzer()
                            
                            # Step 1: Comprehensive code analysis
                            print("📊 Analyzing entire codebase...")
                            code_summary = a.summarize_codebase(github_url)
                            
                            if 'error' in code_summary:
                                result = f"Error: {code_summary['error']}"
                            else:
                                features = code_summary['features']
                                
                                # Step 2: Semantic matching
                                print(f"🔍 Matching {len(features)} features to {len(tasks)} tasks...")
                                matches = a.match_features_to_tasks(features, tasks)
                                
                                # Step 3: Update tasks
                                updated_count = 0
                                result = "🔍 **Semantic Code Analysis Complete**\n\n"
                                result += f"Analyzed {code_summary['total_files']} files\n"
                                result += f"Found {len(features)} features\n\n"
                                result += "**Task Updates:**\n\n"
                                
                                for match in matches:
                                    if match['task']:
                                        task = match['task']
                                        old_status = task['status']
                                        new_status = match['new_status']
                                        
                                        result += f"**{task['title']}**\n"
                                        result += f"  Implemented: {match['implemented']}\n"
                                        result += f"  Status: {old_status} → {new_status}\n"
                                        result += f"  Evidence: {match['evidence']}\n"
                                        result += f"  Confidence: {match['confidence']}\n\n"
                                        
                                        # Update if status changed
                                        if old_status != new_status and match['confidence'] in ['High', 'Medium']:
                                            task['status'] = new_status
                                            updated_count += 1
                                            print(f"  ✓ {task['title']}: {old_status} → {new_status}")
                                
                                # Save updates
                                if updated_count > 0:
                                    self.db.save_project(self.current_project)
                                    result += f"\n✅ **Updated {updated_count} task(s)**"
                                else:
                                    result += "\n📝 No status changes needed"
                            
                        except Exception as e:
                            result = f"Error: {str(e)}"
                            print(f"❌ Error: {e}")
                            import traceback
                            traceback.print_exc()

            elif tool_name == "search_research_papers_tool":
                result = search_research_papers_tool.invoke(tool_args)

            elif tool_name == "generate_literature_review_tool":
                result = generate_literature_review_tool.invoke(tool_args)
            
            else:
                result = f"Tool {tool_name} not implemented"
            
            results.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_id,
                    name=tool_name
                )
            )
        
        return {"messages": results}
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """
        Decide if we should continue to tools or end
        """
        last_message = state["messages"][-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    def start_session(self, project_id: str = None):
        """Start a new session"""
        if project_id:
            self.current_project_id = project_id
            self.current_project = self.db.get_project(project_id)
            
            # Load memory
            context = self.memory.load_context(project_id)
            print(f"\n📚 Memory Loaded:\n{context}\n")
        else:
            self.current_project_id = str(uuid.uuid4())
            self.current_project = None
    
    def chat(self, user_input: str) -> str:
        """
        Main chat function - uses agentic workflow
        """
        # Track user message for session memory
        self.messages_history.append({'role': 'user', 'content': user_input})
        
        # Create initial state
        state = {
            "messages": [HumanMessage(content=user_input)],
            "project_id": self.current_project_id,
            "current_project": self.current_project or {}
        }
        
        # Run the agentic workflow
        final_state = self.app.invoke(state)
        
        # Extract the last AI message
        last_message = final_state["messages"][-1]
        
        # Update current project if it changed
        if final_state.get("current_project"):
            self.current_project = final_state["current_project"]
        
        # Extract clean text from response
        content = last_message.content
        
        # Handle structured response format
        if isinstance(content, list):
            # Extract text from list of content blocks
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
            content = '\n'.join(text_parts) if text_parts else str(content)
        
        # Track AI response for session memory
        self.messages_history.append({'role': 'assistant', 'content': content})
        
        return content
    
    def end_session(self):
        """End session and save to memory"""
        if not self.messages_history:
            print("No messages to save")
            return
        
        # Convert conversation to message format for memory
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = []
        for msg in self.messages_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            else:
                messages.append(AIMessage(content=msg['content']))
        
        if messages and self.current_project_id:
            session = self.memory.save_session(self.current_project_id, messages)
            print(f"\n💾 Session Saved!")
            print(f"Summary: {session['summary']}\n")
        else:
            print("No session to save")