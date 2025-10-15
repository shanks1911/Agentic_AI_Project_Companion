from typing import TypedDict, List, Dict
import os
import time
import chromadb
import base64
from dotenv import load_dotenv
from github import Auth, Github, GithubException
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

import google.generativeai as genai

# --- 1. SETUP: Load environment variables and initialize models ---
load_dotenv()

# Ensure keys are set before use
google_api_key = os.getenv("GOOGLE_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")

if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not set in .env file")
if not github_token:
    raise ValueError("GITHUB_TOKEN not set in .env file")

genai.configure(api_key=google_api_key)

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize the Gemini model and embeddings
# Note: Ensure you are using a model that fits your needs. Flash is fast and efficient.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Initialize GitHub client
auth = Auth.Token(github_token)
g = Github(auth=auth)


# --- 2. DEFINE THE STATE ---
class GraphState(TypedDict):
    repo_url: str
    repo_contents: List[Dict]
    documents: List[Document]
    project_summary: str
    error: str


# --- 3. DEFINE THE NODES ---

def fetch_repo_contents(state: GraphState) -> GraphState:
    """Fetches the content of all relevant files in a GitHub repository."""
    print("--- 🔎 Fetching Repository Contents ---")
    try:
        repo_url = state['repo_url']
        repo_path = repo_url.split("github.com/")[-1]
        repo = g.get_repo(repo_path)
        contents = repo.get_contents("")
        
        repo_data = []
        files_to_process = []
        
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                # Filter for common code/text files and ignore large files
                if (file_content.path.endswith(('.py', '.js', '.ts', '.md', 'Dockerfile', '.yml', '.yaml', '.java', '.go', '.rs')) and
                    file_content.size > 0 and file_content.size < 100000): # Increased size limit slightly
                    files_to_process.append(file_content)

        print(f"Found {len(files_to_process)} files to process.")
        
        for file in files_to_process:
            try:
                content = base64.b64decode(file.content).decode('utf-8')
                repo_data.append({"path": file.path, "content": content})
            except (UnicodeDecodeError, ValueError) as e:
                print(f"Could not decode file {file.path}, skipping. Error: {e}")
                
        return {**state, "repo_contents": repo_data}

    except GithubException as e:
        print(f"GitHub API Error: {e.status} - {e.data}")
        return {**state, "error": f"Failed to fetch repository: {str(e)}"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {**state, "error": f"An unexpected error occurred: {str(e)}"}


def analyze_and_summarize(state: GraphState) -> GraphState:
    """Analyzes the repo content to generate a project summary and individual file summaries."""
    print("--- 🤖 Analyzing and Summarizing Code ---")
    if not state.get("repo_contents"):
        return {**state, "error": "No repository content to analyze."}

    # Create a string with all file paths and contents for context
    # Limit content length to avoid overwhelming the context window
    full_repo_context = "\n\n".join(
        [f"File: {item['path']}\n\n```\n{item['content'][:3000]}\n```" for item in state['repo_contents']]
    )

    ## --- UPDATED PROMPT ---
    # This new prompt asks for purpose, functionality, and architecture instead of just libraries.
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior software architect. Your task is to provide a clear, high-level overview of a software project based on its file structure and code snippets."),
        ("human", """
        Based on the provided repository context, please generate the following:

        1. **Project Purpose:** In one or two sentences, what is the main goal of this project? What problem does it solve?
        2. **Core Functionality:** As a bulleted list, describe the key features or capabilities of this software.
        3. **Architecture Overview:** Briefly describe how the project is structured. How do the main files and directories interact? (e.g., 'This appears to be a web application with a frontend in 'src/', a backend API in 'api/', and configuration in 'docker-compose.yml'.')
        
        Repository Context:
        {context}
        """)
    ])
    
    summary_chain = summary_prompt | llm
    project_summary = summary_chain.invoke({"context": full_repo_context}).content
    print(f"Project Summary:\n{project_summary}")

    ## --- UPDATED PROMPT ---
    # This new prompt adds a "Dependencies & Interactions" section to understand the file's context.
    file_summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a code documentation expert. Your task is to analyze a single code file and explain its purpose and functionality within the broader project."),
        ("human", """
        Please analyze the following file and provide a structured summary.

        **File Path:** `{path}`

        **Content:**
        ```
        {content}
        ```

        Provide the following analysis:
        1. **File Purpose:** A concise, one-sentence description of this file's primary role.
        2. **Key Functions/Components:** A bulleted list of the main functions, classes, or components in this file. For each, provide a brief (1-line) description of what it does.
        3. **Dependencies & Interactions:** How does this file connect to other parts of the project? Mention any important modules it imports from within the project or how other files might use it.
        """)
    ])
    
    analysis_chain = file_summary_prompt | llm
    
    documents = []
    
    for item in state['repo_contents']:
        # Ensure content is not empty
        if not item['content'].strip():
            continue
            
        # Generate a structured summary for the file
        file_summary = analysis_chain.invoke({"path": item['path'], "content": item['content']}).content
        
        # Create a LangChain Document with the detailed summary
        doc = Document(
            page_content=file_summary,
            metadata={
                "source": item['path'],
                "code_snippet": item['content']
            }
        )
        documents.append(doc)
    
    print(f"Created {len(documents)} documents with detailed summaries.")
    return {**state, "project_summary": project_summary, "documents": documents}


def store_in_chroma(state: GraphState) -> GraphState:
    """Stores the generated documents into a ChromaDB vector store."""
    print("--- 💾 Storing Documents in ChromaDB ---")
    if not state.get("documents"):
        print("No documents were generated to store.")
        return state # Return state without error if summarization produced no documents
    
    # Define collection name from repo URL, cleaning it for ChromaDB
    repo_name = state['repo_url'].split("/")[-1].replace('.', '_')
    collection_name = f"repo_{repo_name}"
    
    vectorstore = Chroma.from_documents(
        documents=state['documents'],
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./chroma_db"
    )
    
    print(f"Successfully stored {len(state['documents'])} documents in collection '{collection_name}'.")
    return state


# --- 4. BUILD AND COMPILE THE GRAPH ---
workflow = StateGraph(GraphState)

# Add the nodes to the graph
workflow.add_node("fetch_repo_contents", fetch_repo_contents)
workflow.add_node("analyze_and_summarize", analyze_and_summarize)
workflow.add_node("store_in_chroma", store_in_chroma)

# Set the entry point and define the edges
workflow.set_entry_point("fetch_repo_contents")
workflow.add_edge("fetch_repo_contents", "analyze_and_summarize")
workflow.add_edge("analyze_and_summarize", "store_in_chroma")
workflow.add_edge("store_in_chroma", END)

# Compile the graph into a runnable app
app = workflow.compile()


# --- 5. RUN THE AGENT ---
if __name__ == "__main__":
    repo_url = "https://github.com/shanks1911/LangGraph_Learning" # Example of a more complex repository
    inputs = {"repo_url": repo_url}
    
    final_state = app.invoke(inputs)

    if final_state.get("error"):
        print(f"\n--- 🚨 An error occurred ---")
        print(final_state["error"])
    else:
        print("\n--- ✅ Agent execution complete ---")
        print(f"Project: {repo_url}")
        print("\n--- Project Summary ---")
        print(final_state.get("project_summary", "Not available."))

# This new section will run after the main agent work is done.
    # Add a brief pause as requested.
    print("\n--- ⏳ Pausing for 3 seconds before viewing stored documents ---")
    time.sleep(3)

    print("\n--- 📄 Viewing Documents from ChromaDB ---")
    
    # Initialize collection_name to None for the except block
    collection_name = None
    try:
        # --- CORRECTED LINE ---
        # Dynamically determine the collection name, ensuring it MATCHES the saving logic.
        repo_name = repo_url.split("/")[-1] # REMOVED .replace('.', '_')
        collection_name = f"repo_{repo_name}"

        # Connect to the persisted ChromaDB client
        print(f"DEBUG: Connecting to ChromaDB at path './chroma_db'...")
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Load the specific collection
        print(f"DEBUG: Attempting to load collection: '{collection_name}'...")
        collection = client.get_collection(collection_name)
        print("DEBUG: Collection loaded successfully.")

        # Fetch all documents and their metadata from the collection
        docs = collection.get(include=["documents", "metadatas"])

        if not docs or not docs.get("documents"):
            print("\nINFO: No documents found in the collection. The process may have run correctly but generated no summaries.")
        else:
            print(f"\nTotal summaries stored: {len(docs['documents'])}\n")

            # Loop through and print each document's summary and source
            for i, doc_content in enumerate(docs["documents"]):
                metadata = docs["metadatas"][i]
                source_file = metadata.get("source", "Unknown")
                code_preview = metadata.get('code_snippet', 'Not available')[:250] # Preview first 250 chars

                print(f"--- Document {i+1}: {source_file} ---")
                print(f"Analysis/Summary:\n{doc_content}\n")
                print(f"Original Code Snippet (Preview):\n```\n{code_preview}...\n```\n")

    except Exception as e:
        print(f"\n--- 🚨 An error occurred while trying to view documents ---")
        if collection_name:
            print(f"Could not read from ChromaDB. Please ensure the collection '{collection_name}' exists and is not empty.")
        print(f"Error details: {e}")