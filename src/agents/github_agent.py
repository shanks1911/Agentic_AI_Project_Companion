#github_agent.py
from typing import TypedDict, List, Dict
import os
import base64
from dotenv import load_dotenv
from github import Auth, Github, GithubException
from langgraph.graph import StateGraph, END

# --- Memory ---
from src.database.mongo_vector_store import MongoVectorMemory

# --- LLM (centralized) ---
from src.core.llm import get_llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document


# --- 1. SETUP ---
load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")

if not github_token:
    raise ValueError("GITHUB_TOKEN not set in .env file")

llm = get_llm()

auth = Auth.Token(github_token)
g = Github(auth=auth)

# ✅ Central vector memory
memory = MongoVectorMemory()


# --- 2. STATE ---
class GraphState(TypedDict):
    repo_url: str
    repo_contents: List[Dict]
    documents: List[Document]
    project_summary: str
    error: str


# --- 3. NODES ---

def fetch_repo_contents(state: GraphState) -> GraphState:
    """Fetch repository files"""

    print("--- 🔎 Fetching Repository Contents ---")

    try:
        from urllib.parse import urlparse

        repo_url = state["repo_url"]

        parsed = urlparse(repo_url)

        if parsed.netloc != "github.com":
            return {**state, "error": "Invalid GitHub URL"}

        parts = parsed.path.strip("/").split("/")

        if len(parts) < 2:
            return {**state, "error": "Invalid GitHub URL"}

        repo_path = f"{parts[0]}/{parts[1]}"

        repo = g.get_repo(repo_path)
        contents = repo.get_contents("")

        repo_data = []
        files_to_process = []

        while contents:
            file_content = contents.pop(0)

            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                if (
                    file_content.path.endswith(
                        ('.py', '.js', '.ts', '.md', 'Dockerfile', '.yml', '.yaml', '.java', '.go', '.rs')
                    )
                    and file_content.size > 0
                    and file_content.size < 100000
                ):
                    files_to_process.append(file_content)

        print(f"Found {len(files_to_process)} files")

        for file in files_to_process:
            try:
                content = base64.b64decode(file.content).decode("utf-8")
                repo_data.append({
                    "path": file.path,
                    "content": content
                })
            except Exception:
                continue

        return {**state, "repo_contents": repo_data}

    except GithubException as e:
        return {**state, "error": f"GitHub Error: {str(e)}"}

    except Exception as e:
        return {**state, "error": str(e)}


def analyze_and_summarize(state: GraphState) -> GraphState:
    """Analyze repository with LLM"""

    print("--- 🤖 Analyzing Code ---")

    if not state.get("repo_contents"):
        return {**state, "error": "No content found"}

    full_context = "\n\n".join([
        f"File: {f['path']}\n{f['content'][:3000]}"
        for f in state["repo_contents"]
    ])

    # Project-level summary
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior software architect."),
        ("human", """
        Analyze this repository and provide:

        1. Project Purpose
        2. Core Features
        3. Tech Stack (IMPORTANT)
        4. Architecture Overview

        {context}
        """)
    ])

    summary = (summary_prompt | llm).invoke({
        "context": full_context
    }).content

    # File-level analysis
    file_prompt = ChatPromptTemplate.from_messages([
        ("system", "You analyze code files."),
        ("human", """
        File: {path}

        Content:
        {content}

        Provide:
        - Purpose
        - Key functions/classes
        - Dependencies/interactions
        """)
    ])

    documents = []

    for f in state["repo_contents"]:
        try:
            file_summary = (file_prompt | llm).invoke({
                "path": f["path"],
                "content": f["content"]
            }).content

            documents.append(Document(
                page_content=file_summary,
                metadata={
                    "source": f["path"]
                }
            ))
        except Exception:
            continue

    return {
        **state,
        "project_summary": summary,
        "documents": documents
    }


def store_in_chroma(state: GraphState) -> GraphState:
    """Store into central vector memory"""

    print("--- 💾 Storing in Vector Memory ---")

    if not state.get("documents"):
        return state

    repo_url = state["repo_url"]

    for doc in state["documents"]:
        try:
            memory.add_memory(
                text=doc.page_content,
                metadata={
                    "project_id": repo_url,
                    "source": doc.metadata.get("source"),
                    "type": "github_analysis"
                }
            )
        except Exception as e:
            print(f"Memory error: {e}")

    print(f"✅ Stored {len(state['documents'])} documents")

    return state


# --- 4. GRAPH ---
workflow = StateGraph(GraphState)

workflow.add_node("fetch_repo_contents", fetch_repo_contents)
workflow.add_node("analyze_and_summarize", analyze_and_summarize)
workflow.add_node("store_in_chroma", store_in_chroma)

workflow.set_entry_point("fetch_repo_contents")
workflow.add_edge("fetch_repo_contents", "analyze_and_summarize")
workflow.add_edge("analyze_and_summarize", "store_in_chroma")
workflow.add_edge("store_in_chroma", END)

app = workflow.compile()


# --- 5. WRAPPER FOR ORCHESTRATOR ---
def run_github_analysis(repo_url: str) -> Dict:
    """Entry point for orchestrator"""

    try:
        result = app.invoke({"repo_url": repo_url})

        if result.get("error"):
            return {
                "success": False,
                "error": result["error"]
            }

        return {
            "success": True,
            "summary": result.get("project_summary", ""),
            "documents_count": len(result.get("documents", []))
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }