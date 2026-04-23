# src/orchestrator_agent.py
"""
Central multi-agent orchestrator for the Agentic AI Project Assistant.

This module coordinates specialized agents through a LangGraph workflow and
serves as the main intelligence layer of the system. It evaluates user intent,
loads relevant memory, and routes each request to the most suitable agent.

Integrated agents:
- Planner Agent: generates project plans, tasks, timelines, and diagrams
- Research Agent: finds papers and creates literature reviews
- GitHub Agent: analyzes repositories and codebases
- Idea Agent: handles follow-up requests, summaries, refinements, and guidance

Core responsibilities:
- Maintain active project session state
- Inject historical and semantic memory into prompts
- Route requests using rules + LLM fallback supervision
- Persist project data and conversations
- Manage session lifecycle (start, chat, end)
- Provide a single backend interface for the frontend UI
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from src.agents.github_agent import run_github_analysis

import json
import re
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

from src.database.mongo_db import MongoDB
from src.memory.memory import Memory

from src.agents.planner_agent import generate_project_plan_tool


from src.core.llm import get_llm
from src.agents.idea_agent import idea_followup_tool

from src.agents.research_agent import (
    search_research_papers_tool,
    generate_literature_review_tool
)

# ---------------------------------------------------
# Agent State
# ---------------------------------------------------

class AgentState(TypedDict):
    """
    Shared LangGraph state passed between orchestrator nodes.

    Attributes:
        messages: Conversation messages exchanged in current run.
        project_id: Active project identifier.
        current_project: Current project metadata and saved state.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    project_id: str
    current_project: dict


# ---------------------------------------------------
# Orchestrator
# ---------------------------------------------------

class AgenticOrchestrator:
    """
    Main controller that manages agent routing, memory, persistence,
    and user conversation flow.
    """
    def __init__(self):

        self.llm = get_llm()

        self.db = MongoDB()
        self.memory = Memory(self.db)

        self.current_project_id = None
        self.current_project = None
        self.messages_history = []

        self.app = self._build_graph()


# ---------------------------------------------------
# Build Graph
# ---------------------------------------------------

    def _build_graph(self):
        """
        Construct and compile the LangGraph workflow.

        Returns:
            Compiled graph application with supervisor routing.
        """
        workflow = StateGraph(AgentState)

        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("planner_agent", self.planner_agent)
        workflow.add_node("research_agent", self.research_agent)
        workflow.add_node("github_agent", self.github_agent)
        workflow.add_node("idea_agent", self.idea_agent)

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            self.route_agent,
            {
                "planning": "planner_agent",
                "research": "research_agent",
                "github": "github_agent",
                "idea": "idea_agent",
                "end": END
            }
        )

        workflow.add_edge("planner_agent", END)
        workflow.add_edge("research_agent", END)
        workflow.add_edge("github_agent", END)
        workflow.add_edge("idea_agent", END)

        return workflow.compile()


# ---------------------------------------------------
# Supervisor Agent
# ---------------------------------------------------

    def supervisor_node(self, state: AgentState):
        """
        Inspect the latest user message and decide which specialist
        agent should handle the request.

        Uses deterministic keyword routing first, then falls back to
        an LLM supervisor when intent is ambiguous.

        Args:
            state: Current workflow state.

        Returns:
            Updated state containing routing decision message.
        """
        user_input = ""

        # Get latest real user message
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_input = msg.content.lower().strip()
                break

        # ==================================================
        # HARD RULES (prevent wrong LLM routing)
        # ==================================================

        how_keywords = [
            "how to", "how do i", "how can i",
            "implement", "explain", "guide me",
            "best way", "help me build","make system", "i want to build", "i want to create"
        ]

        followup_keywords = [
            "summary", "summarize", "clarify",
            "refine", "improve", "compare",
            "simplify", "why", "what next",
            "tell me more", "details",
            "can you explain", "elaborate"
        ]

        planning_keywords = [
            "generate plan", "project plan",
            "roadmap", "timeline",
            "create tasks", "milestones",
            "task breakdown", "full plan",
            "build project plan"
        ]

        research_keywords = [
            "literature review", "research paper",
            "papers on", "survey paper",
            "recent papers", "academic papers"
        ]


        # ---------- GitHub ----------
        if "github.com/" in user_input:
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"github","reason":"GitHub URL detected"}')
                ]
            }

        # ---------- Research ----------
        if any(k in user_input for k in research_keywords):
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"research","reason":"research request"}')
                ]
            }


        # ---------- Planning ----------
        if any(k in user_input for k in planning_keywords):
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"planning","reason":"planning request"}')
                ]
            }

        # ---------- Idea / Follow-up ----------
        if any(k in user_input for k in how_keywords):
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"idea","reason":"implementation/how-to request"}')
                ]
            }

        if any(k in user_input for k in followup_keywords):
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"idea","reason":"follow-up request"}')
                ]
            }

        # ==================================================
        # LLM FALLBACK
        # ==================================================

        system_prompt = """
    You are a supervisor agent.

    Choose best agent.

    Agents:

    planning → create plans, tasks, milestones, timelines

    research → papers, literature review, surveys

    github → repository/code/GitHub analysis

    idea → implementation help, summaries, explanations,
    follow-up questions, refinements, comparisons

    IMPORTANT:
    If unsure, choose idea.

    Return JSON ONLY:

    {
    "agent":"planning | research | github | idea | end",
    "reason":"why"
    }
    """

        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

        response = self.llm.invoke(messages)

        return {"messages": state["messages"] + [response]}

# ---------------------------------------------------
# Routing Logic
# ---------------------------------------------------

    def route_agent(self, state: AgentState) -> Literal[
        "planning",
        "research",
        "github",
        "idea",
        "end"
    ]:

        """
        Convert supervisor decision output into graph route labels.

        Args:
            state: Current workflow state.

        Returns:
            Next node name.
        """

        decision_text = state["messages"][-1].content

        try:
            parsed = json.loads(decision_text)
            decision = parsed.get("agent", "").lower()
        except:
            decision = decision_text.lower()

        if "planning" in decision:
            return "planning"

        if "research" in decision:
            return "research"

        if "github" in decision:
            return "github"

        if "idea" in decision:
            return "idea"
        
        return "end"


# ---------------------------------------------------
# Planner Agent
# ---------------------------------------------------

    def planner_agent(self, state: AgentState):
        """
        Generate a structured project plan from conversation context
        and persist the resulting project data.

        Args:
            state: Current workflow state.

        Returns:
            AI response containing generated plan JSON.
        """
        conversation = "\n".join([m.content for m in state["messages"]])

        project_context = state["current_project"]

        conversation += f"""

        Current Project:
        {project_context}
        """

        result = generate_project_plan_tool.invoke({
            "conversation_context": conversation
        })

        try:
            project_data = json.loads(result)

            project_data["id"] = state["project_id"]

            # Save to MySQL
            self.db.save_project(project_data)

            # Update current project in memory
            self.current_project = project_data

        except Exception as e:
            print("Error saving project:", e)

        return {"messages": [AIMessage(content=result)]}


# ---------------------------------------------------
# Research Agent
# ---------------------------------------------------

    def research_agent(self, state: AgentState):
        """
        Build a research query from user intent and generate a
        literature review using the research tools.

        Args:
            state: Current workflow state.

        Returns:
            AI response containing research output.
        """
        raw_input = state["messages"][0].content.lower()

        # Extract meaningful keywords
        keywords = []

        if "email" in raw_input:
            keywords.append("email")

        if "response" in raw_input:
            keywords.append("response generation")

        if "automated" in raw_input:
            keywords.append("automation")

        if "nlp" in raw_input or "language" in raw_input:
            keywords.append("natural language processing")

        # fallback
        if not keywords:
            keywords = raw_input.split()[:5]

        query = " ".join(keywords)

        result = generate_literature_review_tool.invoke({
            "query": query,
            "project_description": state["current_project"].get("description", query)
        })

        return {"messages": [AIMessage(content=result)]}


# ---------------------------------------------------
# GitHub Agent
# ---------------------------------------------------

    def github_agent(self, state: AgentState):
        """
        Detect a GitHub repository URL from user input, run repository
        analysis, and return a summarized report.

        Args:
            state: Current workflow state.

        Returns:
            AI response with repository insights or error message.
        """
        # ✅ 1. Extract LAST HUMAN MESSAGE (CRITICAL FIX)
        user_input = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        if not user_input:
            return {
                "messages": [
                    AIMessage(content="❌ No user input found.")
                ]
            }

        user_input = user_input.strip()

        print("REAL USER INPUT >>>", repr(user_input))

        # ✅ 2. Robust GitHub URL extraction
        match = re.search(r'https://github\.com/[^\s]+', user_input)

        if not match:
            return {
                "messages": [
                    AIMessage(content=f"❌ Could not detect GitHub URL in: {user_input}")
                ]
            }

        github_url = match.group(0).rstrip('.,)\n ')

        print("EXTRACTED URL:", github_url)

        # ✅ 3. Run analysis
        result = run_github_analysis(github_url)

        if not result["success"]:
            return {
                "messages": [
                    AIMessage(content=f"❌ Error analyzing repository: {result['error']}")
                ]
            }

        # ✅ 4. Final response
        response = f"""
    📊 **GitHub Repository Analysis**

    🔗 Repo: {github_url}

    📌 **Project Summary:**
    {result['summary']}

    📄 Documents Stored in Memory: {result['documents_count']}

    🧠 You can now ask:
    - Tech stack used
    - File-level explanations
    - Feature breakdown
    """

        return {"messages": [AIMessage(content=response)]}
        

    

# ---------------------------------------------------
# Idea Agent
# ---------------------------------------------------

    def idea_agent(self, state: AgentState):
        """
        Handle conversational follow-up requests such as summaries,
        refinements, implementation help, and comparisons.

        Args:
            state: Current workflow state.

        Returns:
            AI response generated by idea follow-up tool.
        """
        user_input = ""

        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        # ✅ Better fallback context from memory
        project_context = state.get("current_project", {}) or {}

        if not project_context:
            memory_context = self.memory.retrieve_semantic_memory(
                "project idea current project startup idea",
                state["project_id"]
            )

            if memory_context:
                project_context = {
                    "memory_context": memory_context
                }

        result = idea_followup_tool.invoke({
            "user_input": user_input,
            "project_context": json.dumps(project_context)
        })

        return {"messages": [AIMessage(content=result)]}


# ---------------------------------------------------
# Session Management
# ---------------------------------------------------

    def start_session(self, project_id=None):
        """
        Start a new project session or load an existing one.

        Args:
            project_id: Existing project ID to resume.
        """


        if project_id:
            self.current_project_id = project_id
            self.current_project = self.db.get_project(project_id)

            context = self.memory.load_context(project_id)
            print("\nMemory Loaded:\n", context)
            return

        # ✅ Create project immediately
        new_id = str(uuid.uuid4())

        project = {
            "id": new_id,
            "title": "Untitled Project",
            "description": "New project session",
            "tasks": [],
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }

        self.db.save_project(project)

        self.current_project_id = new_id
        self.current_project = project


# ---------------------------------------------------
# Chat Entry
# ---------------------------------------------------

    def chat(self, user_input: str):
        """
        Main conversation entry point used by the frontend.

        Loads memory context, invokes the graph workflow, updates
        rolling memory, and returns the final response.

        Args:
            user_input: Latest user message.

        Returns:
            Assistant response string.
        """
        print("USER INPUT:", user_input)

        self.messages_history.append({
            "role": "user",
            "content": user_input
        })
        

        # Retrieve memory context
        session_context = self.memory.load_context(self.current_project_id)

        recent_context = self.memory.get_recent_transcript(self.current_project_id)

        vector_context = self.memory.retrieve_semantic_memory(
            user_input,
            self.current_project_id
        )

        project_context = ""

        if self.current_project:
            project_context = f"""
            Project Info
            Title: {self.current_project.get('title')}
            Description: {self.current_project.get('description')}
            Tech Stack: {self.current_project.get('tech_stack')}
            GitHub: {self.current_project.get('github_url')}
            """

        system_context = f"""
        Previous Sessions:
        {session_context}

        Recent Conversation:
        {recent_context}
        
        Relevant Memory:
        {vector_context}

        {project_context}
        """

        state = {
            "messages": [
                SystemMessage(content=system_context),
                HumanMessage(content=user_input)
            ],
            "project_id": self.current_project_id,
            "current_project": self.current_project or {}
        }

        result = self.app.invoke(state)
        print("RAW RESULT:", result)
        last_message = result["messages"][-1]

        content = last_message.content if last_message.content else "⚠️ No response generated. Try rephrasing."

        self.messages_history.append({
            "role": "assistant",
            "content": content
        })

        # Auto rename first untitled project
        if self.current_project and self.current_project["title"] == "Untitled Project":
            self.current_project["title"] = user_input[:50]
            self.current_project["description"] = user_input
            self.db.save_project(self.current_project)

        if len(self.messages_history) > 20:
            self.messages_history = self.messages_history[-20:]

        # ✅ LIVE MEMORY UPDATE AFTER EACH CHAT TURN
        try:
            latest_messages = [
                HumanMessage(content=user_input),
                AIMessage(content=content)
            ]

            self.memory.save_session(
                self.current_project_id,
                latest_messages
            )

        except Exception as e:
            print("Live memory update error:", e)

        return content


# ---------------------------------------------------
# End Session
# ---------------------------------------------------

    def end_session(self):
        """
        Persist the final conversation history and close active
        rolling sessions for the current project.
        """
        if not self.messages_history:
            return

        messages = []

        for m in self.messages_history:

            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))

            else:
                messages.append(AIMessage(content=m["content"]))

        session = self.memory.save_session(
            self.current_project_id,
            messages
        )

        # ✅ Mark rolling session closed
        self.memory.mongo.sessions.update_many(
            {
                "project_id": self.current_project_id,
                "active": True
            },
            {
                "$set": {"active": False}
            }
        )
