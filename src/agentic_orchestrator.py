# src/agentic_orchestrator.py

from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from src.tools.github_analyzer import run_github_analysis

import json
import re
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

from src.database.mysql_db import MySQLDB
from src.memory.demo_memory import DemoMemory

from src.tools.agent_tools import (
    generate_project_plan_tool,
    link_github_repository_tool,
    get_project_status_tool
)

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
    messages: Annotated[Sequence[BaseMessage], add_messages]
    project_id: str
    current_project: dict


# ---------------------------------------------------
# Orchestrator
# ---------------------------------------------------

class AgenticOrchestrator:

    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY"),
            temperature=0.3
        )

        self.db = MySQLDB()
        self.memory = DemoMemory(self.db)

        self.current_project_id = None
        self.current_project = None
        self.messages_history = []

        self.app = self._build_graph()


# ---------------------------------------------------
# Build Graph
# ---------------------------------------------------

    def _build_graph(self):

        workflow = StateGraph(AgentState)

        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("planning_agent", self.planning_agent)
        workflow.add_node("research_agent", self.research_agent)
        workflow.add_node("github_agent", self.github_agent)
        workflow.add_node("status_agent", self.status_agent)
        workflow.add_node("idea_agent", self.idea_agent)

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            self.route_agent,
            {
                "planning": "planning_agent",
                "research": "research_agent",
                "github": "github_agent",
                "status": "status_agent",
                "idea": "idea_agent",
                "end": END
            }
        )

        workflow.add_edge("planning_agent", END)
        workflow.add_edge("research_agent", END)
        workflow.add_edge("github_agent", END)
        workflow.add_edge("status_agent", END)
        workflow.add_edge("idea_agent", END)

        return workflow.compile()


# ---------------------------------------------------
# Supervisor Agent
# ---------------------------------------------------

    def supervisor_node(self, state: AgentState):

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
            "best way", "help me build",
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

        status_keywords = [
            "status", "progress",
            "what is pending", "completed tasks",
            "remaining tasks", "deadline",
            "behind schedule", "project status"
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

        # ---------- Status ----------
        if any(k in user_input for k in status_keywords):
            return {
                "messages": state["messages"] + [
                    AIMessage(content='{"agent":"status","reason":"status request"}')
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

    status → progress, pending work, deadlines

    idea → implementation help, summaries, explanations,
    follow-up questions, refinements, comparisons

    IMPORTANT:
    If unsure, choose idea.

    Return JSON ONLY:

    {
    "agent":"planning | research | github | status | idea | end",
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
        "status",
        "idea",
        "end"
    ]:

        

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

        if "status" in decision:
            return "status"

        if "idea" in decision:
            return "idea"
        
        return "end"


# ---------------------------------------------------
# Planning Agent
# ---------------------------------------------------

    def planning_agent(self, state: AgentState):

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
# Status Agent
# ---------------------------------------------------

    def status_agent(self, state: AgentState):

        result = get_project_status_tool.invoke({})

        return {"messages": [AIMessage(content=result)]}
    

# ---------------------------------------------------
# Idea Agent
# ---------------------------------------------------

    def idea_agent(self, state: AgentState):

        user_input = ""

        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        result = idea_followup_tool.invoke({
            "user_input": user_input,
            "project_context": json.dumps(state.get("current_project", {}))
        })

        return {"messages": [AIMessage(content=result)]}


# ---------------------------------------------------
# Session Management
# ---------------------------------------------------

    def start_session(self, project_id=None):

        if project_id:
            self.current_project_id = project_id
            self.current_project = self.db.get_project(project_id)

            context = self.memory.load_context(project_id)
            print("\nMemory Loaded:\n", context)

        else:
            self.current_project_id = str(uuid.uuid4())
            self.current_project = None


# ---------------------------------------------------
# Chat Entry
# ---------------------------------------------------

    def chat(self, user_input: str):
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

        if len(self.messages_history) > 20:
            self.messages_history = self.messages_history[-20:]

        return content


# ---------------------------------------------------
# End Session
# ---------------------------------------------------

    def end_session(self):

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
