"""
Streamlit UI for Agentic AI Project Assistant
Run: streamlit run streamlit_agentic_demo.py
"""
import streamlit as st
from dotenv import load_dotenv
from src.agentic_orchestrator import AgenticOrchestrator
from datetime import datetime
import plotly.express as px
import pandas as pd
import time
import io
import sys
import json

def render_response(response):
    """
    Smart renderer:
    - If JSON → format nicely
    - Else → show as markdown
    """
    try:
        data = json.loads(response)

        # Check if it's a project plan
        if "title" in data and "tasks" in data:

            st.subheader(f"📌 {data.get('title')}")
            st.write(data.get("description"))

            st.divider()
            st.subheader("📋 Tasks")

            for task in data.get("tasks", []):
                st.markdown(f"**{task['id']}. {task['title']}**")
                st.caption(task['description'])

            return

    except:
        pass

    # fallback (normal response with structure)
    if "## 🔬" in response:
        sections = response.split("##")

        for section in sections:
            if section.strip():
                st.markdown("## " + section.strip())
    else:
        st.markdown(response)

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Project Assistant (Agentic)",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .agentic-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .tool-call {
        border-left: 4px solid #1f77b4;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .task-item {
        padding: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to process chat
def process_user_message(user_message):
    """Process a user message and get agent response - RETURNS response only"""
    
    # Capture tool usage
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        response = st.session_state.app.chat(user_message)
        
        # Capture tool logs
        output = captured_output.getvalue()
        sys.stdout = old_stdout
        
        if "🔧 Agent is using tool:" in output:
            for line in output.split('\n'):
                if '🔧 Agent is using tool:' in line:
                    tool_name = line.split(':')[-1].strip()
                    if tool_name not in st.session_state.tool_logs[-5:]:  # Avoid duplicates
                        st.session_state.tool_logs.append(tool_name)
        
        return response
        
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {str(e)}"

# Initialize session state
if 'app' not in st.session_state:
    st.session_state.app = AgenticOrchestrator()
    st.session_state.chat_history = []
    st.session_state.current_project_id = None
    st.session_state.tool_logs = []
    st.session_state.pending_message = None 

# Header
st.markdown('<div class="main-header">🤖 AI Project Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="agentic-badge">✨ AGENTIC MODE - Agent decides which tools to use</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📂 Projects")
    
    projects = st.session_state.app.db.list_projects()
    
    if projects:
        # Show projects with unique identifiers to distinguish duplicates
        project_display = []
        for p in projects:
            # Safety check for None ID
            if not p.get('id'):
                continue  # Skip projects with no ID
            
            display_name = f"{p['title']}"
            # Add ID suffix if duplicate titles exist
            if sum(1 for proj in projects if proj.get('title') == p['title']) > 1:
                display_name += f" (ID: {p['id'][:8]})"
            project_display.append(display_name)
        
        project_display.insert(0, "➕ New Project")
        
        selected = st.selectbox(
            "Select or create project:",
            project_display,
            key="project_selector"
        )
        
        if selected == "➕ New Project":
            if st.button("Start New Project", use_container_width=True):
                st.session_state.app.start_session()
                st.session_state.chat_history = []
                st.session_state.tool_logs = []
                st.session_state.current_project_id = st.session_state.app.current_project_id
                st.rerun()
        else:
            # Match by display name (handles duplicates with ID suffix)
            if "(ID:" in selected:
                # Extract ID from display name
                project_id = selected.split("(ID: ")[1].rstrip(")")
                selected_proj = next((p for p in projects if p['id'].startswith(project_id)), None)
            else:
                # Match by title
                selected_proj = next((p for p in projects if p['title'] == selected), None)
            
            if selected_proj and st.session_state.current_project_id != selected_proj['id']:
                try:
                    st.session_state.app.start_session(project_id=selected_proj['id'])
                    st.session_state.current_project_id = selected_proj['id']
                    st.session_state.chat_history = []
                    st.session_state.tool_logs = []
                    
                    # Verify project loaded
                    if st.session_state.app.current_project:
                        st.success("📚 Project loaded successfully")
                    else:
                        st.error("⚠️ Failed to load project")
                        
                except Exception as e:
                    st.error(f"Error loading project: {str(e)}")
                    st.session_state.app.start_session()  # Fallback to new project
                    st.session_state.current_project_id = st.session_state.app.current_project_id
    else:
        st.info("No projects yet. Start chatting!")
        st.session_state.app.start_session()
        st.session_state.current_project_id = st.session_state.app.current_project_id
    
    st.divider()
    
    # Current project info
    if st.session_state.app.current_project:
        project = st.session_state.app.current_project
        st.subheader("Current Project")
        st.write(f"**{project['title']}**")
        st.caption(project['description'][:100] + "...")
        
        if project.get('github_url'):
            st.write(f"🔗 [{project['github_url']}]({project['github_url']})")
    
    st.divider()
    
    # Tool activity log
    st.subheader("🔧 Agent Activity")
    if st.session_state.tool_logs:
        for log in st.session_state.tool_logs[-5:]:
            st.markdown(f"""
            <div class="tool-call">
                <small>🛠️ <strong>{log}</strong></small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No tools used yet")
    
    st.divider()
    
    if st.button("💾 End Session", use_container_width=True, type="primary"):
        if st.session_state.app.current_project:
            st.session_state.app.end_session()
            st.success("Session saved!")
            time.sleep(1)
            st.rerun()

# Main area
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📋 Tasks", "📚 Research", "ℹ️ About Agentic"])

with tab1:
    st.subheader("Chat with Agentic AI")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            with st.chat_message("user"):
                st.write(msg['content'])
        else:
            with st.chat_message("assistant"):
                render_response(msg['content'])
    
    # Process pending message from buttons FIRST (before input)
    if st.session_state.get('pending_message'):
        user_message = st.session_state.pending_message
        st.session_state.pending_message = None
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(user_message)
        
        # Add to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agent is thinking..."):
                response = process_user_message(user_message)
                render_response(response)
        
        # Add response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        st.rerun()
    
    # Chat input
    user_input = st.chat_input("Type your message...")
    
    if user_input:
        # Display user message immediately
        with st.chat_message("user"):
            st.write(user_input)
        
        # Add to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agent is thinking..."):
                response = process_user_message(user_input)
                render_response(response)
                st.session_state.app.current_project = st.session_state.app.db.get_project(
                    st.session_state.current_project_id
                )
        
        # Add response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        st.rerun()
    
    # Quick actions
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Status", use_container_width=True):
            st.session_state.pending_message = 'Show me the current project status'
            st.rerun()
    
    with col2:
        if st.button("🔍 Search Similar", use_container_width=True):
            st.session_state.pending_message = 'Search for similar projects'
            st.rerun()
    
    with col3:
        if st.button("📝 Generate Plan", use_container_width=True):
            st.session_state.pending_message = 'Generate a detailed project plan based on our conversation'
            st.rerun()
    
    with col4:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.tool_logs = []
            st.rerun()

from datetime import datetime

from datetime import datetime, timedelta

with tab2:
    st.subheader("📋 Project Tasks")

    if st.session_state.app.current_project:
        project = st.session_state.app.current_project
        tasks = project.get('tasks', [])

        today = datetime.today()

        # 🔥 NORMALIZE TASKS (CRITICAL FIX)
        for t in tasks:

            # ---------- STATUS FIX ----------
            if not t.get("status") or t["status"] not in ["To-Do", "In Progress", "Completed"]:
                t["status"] = "To-Do"

            # ---------- DATE FIX ----------
            start = t.get("start_date")
            end = t.get("end_date")

            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d") if start else today
            except:
                start_dt = today

            try:
                end_dt = datetime.strptime(end, "%Y-%m-%d") if end else (start_dt + timedelta(days=3))
            except:
                end_dt = start_dt + timedelta(days=3)

            # Fix past start
            if start_dt < today:
                start_dt = today

            # Fix invalid end
            if end_dt <= start_dt:
                end_dt = start_dt + timedelta(days=3)

            t["start_date"] = start_dt.strftime("%Y-%m-%d")
            t["end_date"] = end_dt.strftime("%Y-%m-%d")

        # ✅ Save normalized data
        st.session_state.app.db.save_project(project)

        # 🔥 OPTIONAL: USER DEADLINE
        st.divider()
        deadline = st.date_input("📅 Project Deadline (optional)")

        if deadline:
            days_per_task = max(1, (deadline - today.date()).days // max(1, len(tasks)))

            for i, t in enumerate(tasks):
                start_dt = today + timedelta(days=i * days_per_task)
                end_dt = start_dt + timedelta(days=days_per_task)

                t["start_date"] = start_dt.strftime("%Y-%m-%d")
                t["end_date"] = end_dt.strftime("%Y-%m-%d")

            st.session_state.app.db.save_project(project)
            st.success("Timeline updated based on deadline")

        # 🔥 SUB-TABS
        subtab1, subtab2, subtab3 = st.tabs(["📝 To-Do List", "📊 Gantt", "🧱 Kanban"])

        # ---------------- TODO LIST ----------------
        with subtab1:
            if tasks:
                st.write(f"**Total Tasks:** {len(tasks)}")

                completed = len([t for t in tasks if t["status"] == "Completed"])
                progress = completed / len(tasks)

                st.progress(progress)
                st.caption(f"{completed} of {len(tasks)} completed")

                st.divider()

                for task in tasks:
                    st.markdown(f"""
                    <div class="task-item">
                        <strong>#{task['id']} - {task['title']}</strong><br>
                        <small>{task['description']}</small><br>
                        <b>Status:</b> {task['status']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No tasks found.")

        # ---------------- GANTT ----------------
        with subtab2:
            st.subheader("📊 Project Timeline")

            gantt_data = []

            for t in tasks:
                gantt_data.append({
                    "Task": t["title"],
                    "Start": t["start_date"],
                    "Finish": t["end_date"],
                    "Status": t["status"]
                })

            df = pd.DataFrame(gantt_data)

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status"
            )

            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        # ---------------- KANBAN ----------------
        with subtab3:
            st.subheader("🧱 Kanban Board")

            def update_task_status(task_id, new_status):
                for t in project["tasks"]:
                    if t["id"] == task_id:
                        t["status"] = new_status

                st.session_state.app.db.save_project(project)

                # Refresh
                st.session_state.app.current_project = st.session_state.app.db.get_project(
                    st.session_state.current_project_id
                )

            # ✅ SAFE FILTERS (fix empty issue)
            todo = [t for t in tasks if t.get("status", "To-Do") == "To-Do"]
            in_progress = [t for t in tasks if t.get("status") == "In Progress"]
            done = [t for t in tasks if t.get("status") == "Completed"]

            col1, col2, col3 = st.columns(3)

            def render_column(title, task_list, color):
                st.markdown(f"### {title}")

                for task in task_list:
                    st.markdown(f"""
                    <div style="
                        background:{color};
                        padding:10px;
                        border-radius:8px;
                        margin-bottom:10px;
                        color:white;
                    ">
                    <strong>{task['title']}</strong><br>
                    <small>{task['description']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    new_status = st.selectbox(
                        f"Update #{task['id']}",
                        ["To-Do", "In Progress", "Completed"],
                        index=["To-Do", "In Progress", "Completed"].index(task["status"]),
                        key=f"status_{task['id']}"
                    )

                    if new_status != task["status"]:
                        update_task_status(task["id"], new_status)
                        st.rerun()

            with col1:
                render_column("📝 To-Do", todo, "#6c757d")

            with col2:
                render_column("🚧 In Progress", in_progress, "#ffc107")

            with col3:
                render_column("✅ Completed", done, "#28a745")

    else:
        st.info("No active project. Start a conversation first.")
        
with tab3 :
            st.subheader("📚 Research Papers & Literature Review")
            
            if st.session_state.app.current_project:
                project = st.session_state.app.current_project
                
                st.write(f"**Project:** {project['title']}")
                st.write(f"**Description:** {project['description']}")
                
                st.divider()
                
                # Search papers section
                st.subheader("🔍 Search Academic Papers")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    search_query = st.text_input(
                        "Research Keywords",
                        placeholder="e.g., machine learning, NLP, computer vision",
                        help="Enter keywords related to your project"
                    )
                
                with col2:
                    max_results = st.number_input(
                        "Max Results",
                        min_value=5,
                        max_value=20,
                        value=10,
                        step=5
                    )
                
                if st.button("🔍 Search Papers", use_container_width=True, type="primary"):
                    if search_query:
                        with st.spinner("Searching academic databases..."):
                            response = process_user_message(
                                f"Search for research papers about: {search_query}. Maximum {max_results} results."
                            )
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response
                            })
                        
                        # Display results in expandable sections
                        st.success("Search complete! Results shown below.")
                        
                        with st.expander("📄 View Search Results", expanded=True):
                            st.markdown(response, unsafe_allow_html=True)
                    else:
                        st.warning("Please enter search keywords")
                
                st.divider()
                
                # Generate literature review section
                st.subheader("📝 Generate Literature Review")
                
                st.info("💡 This will search papers and generate a comprehensive literature review with citations.")
                
                review_query = st.text_area(
                    "Research Topic",
                    placeholder="Describe your research area in detail...",
                    help="Be specific about what aspect of your project needs literature review"
                )
                
                if st.button("📝 Generate Literature Review", use_container_width=True, type="primary"):
                    if review_query:
                        with st.spinner("🔬 Searching papers and generating review... This may take 30-60 seconds..."):
                            project_desc = f"{project['title']}: {project['description']}"
                            
                            response = process_user_message(
                                f"Generate a literature review for: {review_query}. Project context: {project_desc}"
                            )
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response
                            })
                        
                        st.success("✅ Literature review generated!")
                        
                        # Display in nice format
                        with st.expander("📖 View Literature Review", expanded=True):
                            st.markdown(response)
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download as Text",
                            data=response,
                            file_name=f"literature_review_{project['title'].replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("Please describe your research topic")
                
                st.divider()
                
                # Quick actions
                st.subheader("⚡ Quick Research Actions")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔬 Related Work", use_container_width=True):
                        st.session_state.pending_message = f"Search for papers related to {project['title']}"
                        st.rerun()
                
                with col2:
                    if st.button("📊 Survey Papers", use_container_width=True):
                        st.session_state.pending_message = f"Find survey papers about {project['title']}"
                        st.rerun()
                
                with col3:
                    if st.button("🆕 Recent Papers", use_container_width=True):
                        st.session_state.pending_message = f"Find recent papers from 2024-2025 about {project['title']}"
                        st.rerun()
            
            else:
                st.info("📝 Create a project first to access research features!")
                
                if st.button("➕ Create New Project"):
                    st.session_state.app.start_session()
                    st.session_state.chat_history = []
                    st.session_state.tool_logs = []
                    st.session_state.current_project_id = st.session_state.app.current_project_id
                    st.rerun()

# GitHub section
if st.session_state.app.current_project:
    st.divider()
    st.subheader("🔗 GitHub Integration")
    
    current_url = st.session_state.app.current_project.get('github_url', '')
    
    with st.form("github_form"):
        github_url = st.text_input(
            "Repository URL",
            value=current_url,
            placeholder="https://github.com/username/repo"
        )
        
        submitted = st.form_submit_button("Link Repository", use_container_width=True)
        
        if submitted and github_url:
            with st.spinner("Linking repository..."):
                response = process_user_message(f"Analyze this GitHub repository: {github_url}")
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
            st.success("Repository linked! Check chat for details.")
            st.rerun()
    
    # ADD THIS NEW SECTION HERE ↓↓↓
    if st.session_state.app.current_project.get('github_url'):
        st.divider()
        st.subheader("🔍 Code Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Analyze Repository", use_container_width=True):
                github_url = st.session_state.app.current_project['github_url']
                st.session_state.pending_message = f"Analyze the code at {github_url}"
                st.rerun()
        
        with col2:
            if st.button("✅ Update Task Status", use_container_width=True, type="primary"):
                github_url = st.session_state.app.current_project['github_url']
                tasks = st.session_state.app.current_project.get('tasks', [])
                
                import json
                tasks_json = json.dumps(tasks)
                
                with st.spinner("Analyzing code and updating tasks..."):
                    # Add user message
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': 'Update my task statuses based on the code in my GitHub repository'
                    })
                    
                    # Process with agent
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    
                    try:
                        response = st.session_state.app.chat(
                            f"Analyze {github_url} and match code to these tasks: {tasks_json}"
                        )
                        
                        sys.stdout = old_stdout
                        
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response
                        })
                        
                        # Reload project from database to get updated task statuses
                        st.session_state.app.current_project = st.session_state.app.db.get_project(
                            st.session_state.current_project_id
                        )
                        
                    except Exception as e:
                        sys.stdout = old_stdout
                        st.error(f"Error: {str(e)}")
                
                st.success("✅ Tasks updated! Check the Tasks tab to see changes.")
                time.sleep(1)
                st.rerun()
        
        st.caption("💡 Analyze Repository reads your actual code files. Update Task Status matches code to tasks and updates their status.")

with tab4:
    st.subheader("🧠 What Makes This Agentic?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ❌ Traditional (Non-Agentic)
```python
        if 'plan' in user_input:
            generate_plan()
        elif 'github' in user_input:
            link_github()
        # YOU decide the logic
```
        
        **Problems:**
        - Hardcoded decision tree
        - Can't adapt to context
        - No autonomous reasoning
        """)
    
    with col2:
        st.markdown("""
        ### ✅ Agentic (This System)
```python
        agent.invoke(messages)
        # Agent decides:
        # "Idea is clear, I'll use
        #  generate_project_plan_tool"
```
        
        **Benefits:**
        - Agent chooses tools
        - Context-aware decisions
        - Autonomous reasoning
        """)
    
    st.divider()
    
    st.markdown("""
    ### Key Agentic Features:
    
    | Feature | Description |
    |---------|-------------|
    | 🎯 **Autonomous Tool Selection** | Agent decides which tools to use without hardcoded rules |
    | 🔄 **Multi-Step Reasoning** | Can use multiple tools in sequence, evaluating each result |
    | 🧩 **LangGraph State Machine** | Proper agent-tool loop with dynamic workflow |
    | 🔍 **Context-Aware** | Analyzes full conversation history before deciding |
    
    ### Available Tools:
    
    - `generate_project_plan_tool` - Creates structured project plans
    - `link_github_repository_tool` - Connects GitHub repositories
    - `get_project_status_tool` - Retrieves current project information
    - `search_similar_projects_tool` - Finds similar existing projects
    
    **Watch the "Agent Activity" section in the sidebar to see the agent autonomously choosing tools!**
    """)

# Footer
st.divider()
st.caption("🤖 Agentic AI Project Assistant - Powered by LangGraph & Google Gemini | Agent autonomously decides tool usage")