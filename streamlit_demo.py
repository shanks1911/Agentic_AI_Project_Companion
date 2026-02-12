"""
Streamlit UI for AI Project Assistant Demo
Run: streamlit run streamlit_demo.py
"""
import streamlit as st
from dotenv import load_dotenv
from src.demo_orchestrator import DemoOrchestrator
import time

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Project Assistant",
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
        margin-bottom: 2rem;
    }
    .project-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
    }
    .task-item {
        padding: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-todo {
        background-color: #ffc107;
        color: #000;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'app' not in st.session_state:
    st.session_state.app = DemoOrchestrator()
    st.session_state.chat_history = []
    st.session_state.current_project_id = None

# Header
st.markdown('<div class="main-header">🤖 AI Project Assistant</div>', unsafe_allow_html=True)

# Sidebar - Project Selection
with st.sidebar:
    st.header("📂 Projects")
    
    projects = st.session_state.app.db.list_projects()
    
    if projects:
        project_names = [f"{p['title']}" for p in projects]
        project_names.insert(0, "➕ New Project")
        
        selected = st.selectbox(
            "Select or create project:",
            project_names,
            key="project_selector"
        )
        
        if selected == "➕ New Project":
            if st.button("Start New Project", use_container_width=True):
                st.session_state.app.start_session()
                st.session_state.chat_history = []
                st.session_state.current_project_id = st.session_state.app.current_project_id
                st.rerun()
        else:
            # Find selected project
            selected_proj = next(p for p in projects if p['title'] == selected)
            
            if st.session_state.current_project_id != selected_proj['id']:
                st.session_state.app.start_session(project_id=selected_proj['id'])
                st.session_state.current_project_id = selected_proj['id']
                st.session_state.chat_history = []
                
                # Load memory
                context = st.session_state.app.memory.load_context(selected_proj['id'])
                if "no previous sessions" not in context.lower():
                    st.info("📚 Memory loaded from previous sessions")
    else:
        st.info("No projects yet. Start chatting to create one!")
        st.session_state.app.start_session()
        st.session_state.current_project_id = st.session_state.app.current_project_id
    
    st.divider()
    
    # Show current project info
    if st.session_state.app.current_project:
        project = st.session_state.app.current_project
        st.subheader("Current Project")
        st.write(f"**{project['title']}**")
        st.caption(project['description'][:100] + "...")
        
        if project.get('github_url'):
            st.write(f"🔗 [{project['github_url']}]({project['github_url']})")
    
    st.divider()
    
    # End session button
    if st.button("💾 End Session", use_container_width=True, type="primary"):
        if st.session_state.app.messages:
            st.session_state.app.end_session()
            st.success("Session saved!")
            time.sleep(1)
            st.rerun()

# Main area with tabs
tab1, tab2 = st.tabs(["💬 Chat", "📋 Tasks"])

with tab1:
    # Chat interface
    st.subheader("Chat with AI Assistant")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                with st.chat_message("user"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg['content'])
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = st.session_state.app.chat(user_input)
        
        # Add AI response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        st.rerun()
    
    # Quick action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Show Status", use_container_width=True):
            response = st.session_state.app.chat("status")
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            st.rerun()
    
    with col2:
        if st.button("📝 Generate Plan", use_container_width=True):
            response = st.session_state.app.chat("generate plan")
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            st.rerun()
    
    with col3:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

with tab2:
    # Tasks view
    st.subheader("📋 Project Tasks")
    
    if st.session_state.app.current_project:
        project = st.session_state.app.current_project
        tasks = project.get('tasks', [])
        
        if tasks:
            st.write(f"**Total Tasks:** {len(tasks)}")
            st.divider()
            
            for task in tasks:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="task-item">
                            <strong>#{task['id']} - {task['title']}</strong><br>
                            <small>{task['description']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="status-badge status-todo">
                            {task['status']}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No tasks yet. Generate a plan to create tasks!")
    else:
        st.info("No active project. Start a conversation to create one!")
    
    # GitHub integration section
    if st.session_state.app.current_project:
        st.divider()
        st.subheader("🔗 GitHub Integration")
        
        github_url = st.text_input(
            "GitHub Repository URL",
            value=st.session_state.app.current_project.get('github_url', ''),
            placeholder="https://github.com/username/repo"
        )
        
        if st.button("Link Repository"):
            if github_url:
                response = st.session_state.app.chat(github_url)
                st.success("Repository linked!")
                st.rerun()
            else:
                st.error("Please enter a valid GitHub URL")

# Footer
st.divider()
st.caption("🤖 AI Project Assistant Demo - Built with LangGraph & Google Gemini")