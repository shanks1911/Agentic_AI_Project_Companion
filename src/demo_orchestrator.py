from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import os
import uuid
import re

from src.database.simple_db import SimpleDB
from src.memory.demo_memory import DemoMemory

class DemoOrchestrator:
    """Simple orchestrator for demo - no complex LangGraph yet"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY")
        )
        self.db = SimpleDB()
        self.memory = DemoMemory(self.db)
        self.current_project_id = None
        self.current_project = None
        self.messages = []
    
    def start_session(self, project_id: str = None):
        """Start a new session or resume existing project"""
        if project_id:
            # Resume existing project
            self.current_project_id = project_id
            self.current_project = self.db.get_project(project_id)
            
            # Load memory
            context = self.memory.load_context(project_id)
            print(f"\n📚 Memory Loaded:\n{context}\n")
        else:
            # New project
            self.current_project_id = str(uuid.uuid4())
            self.current_project = None
        
        self.messages = []
    
    def chat(self, user_input: str) -> str:
        """Main chat function - routes to appropriate handler"""
        self.messages.append(HumanMessage(content=user_input))
        
        lower_input = user_input.lower()
        
        # Detect intent and route
        if any(word in lower_input for word in ['plan', 'tasks', 'generate']):
            response = self._generate_plan()
        
        elif 'github.com' in user_input:
            response = self._link_github(user_input)
        
        elif any(word in lower_input for word in ['status', 'progress', 'show tasks']):
            response = self._show_status()
        
        else:
            # Default: refine idea
            response = self._refine_idea()
        
        return response
    
    def _refine_idea(self) -> str:
        """Help user refine their project idea"""
        system_prompt = """You are a helpful project planning assistant. 
Help the user refine their project idea by asking clarifying questions about:
- What problem it solves
- Who will use it
- Key features needed
- Technical constraints

Keep responses brief and conversational. Don't ask more than 2 questions at once."""
        
        full_messages = [HumanMessage(content=system_prompt)] + self.messages
        response = self.llm.invoke(full_messages)
        
        self.messages.append(response)
        return response.content
    
    def _generate_plan(self) -> str:
        """Generate project plan using existing agent"""
        # Extract conversation context
        conversation = "\n".join([msg.content for msg in self.messages])
        
        # Use LLM to extract project details
        extract_prompt = f"""Based on this conversation, extract:
1. Project title (short name)
2. Project description (2-3 sentences)
3. Key features/tasks (list 5-7 main tasks)

Conversation:
{conversation}

Format as:
TITLE: [title]
DESCRIPTION: [description]
TASKS:
- [task 1]
- [task 2]
etc.
"""
        
        extraction = self.llm.invoke([HumanMessage(content=extract_prompt)]).content
        
        # Parse the extraction (simple parsing for demo)
        lines = extraction.split('\n')
        title = "Untitled Project"
        description = ""
        tasks = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('TASKS:'):
                current_section = 'tasks'
            elif current_section == 'tasks' and line.startswith('-'):
                task_text = line.replace('-', '').strip()
                if task_text:
                    tasks.append(task_text)
        
        # If parsing failed, use conversation directly
        if not description:
            description = conversation[:200]
        
        # Create project data directly
        from src.schemas import KanbanTask
        
        kanban_tasks = []
        for i, task_text in enumerate(tasks[:7], start=1):
            kanban_tasks.append({
                'id': i,
                'title': task_text[:100],  # Allow longer titles
                'description': task_text,
                'status': 'To-Do'
            })
        
        # If no tasks extracted, create default ones
        if not kanban_tasks:
            kanban_tasks = [
                {'id': 1, 'title': 'Project Setup', 'description': 'Initialize project structure', 'status': 'To-Do'},
                {'id': 2, 'title': 'Core Features', 'description': 'Build main functionality', 'status': 'To-Do'},
                {'id': 3, 'title': 'Testing', 'description': 'Test all features', 'status': 'To-Do'},
                {'id': 4, 'title': 'Deployment', 'description': 'Deploy to production', 'status': 'To-Do'},
            ]
        
        # Save to database
        project_data = {
            'id': self.current_project_id,
            'title': title,
            'description': description,
            'tasks': kanban_tasks,
            'github_url': None
        }
        self.db.save_project(project_data)
        self.current_project = project_data
        
        # Format response
        response = f"✅ **Project Plan Created!**\n\n"
        response += f"**{title}**\n\n"
        response += f"{description}\n\n"
        response += f"**Tasks ({len(kanban_tasks)}):**\n"
        for task in kanban_tasks:
            response += f"\n{task['id']}. **{task['title']}**\n   {task['description']}\n"
        
        ai_msg = AIMessage(content=response)
        self.messages.append(ai_msg)
        return response
    
    def _link_github(self, user_input: str) -> str:
        """Link GitHub repository to project"""
        # Extract GitHub URL
        urls = re.findall(r'https://github\.com/[\w-]+/[\w-]+', user_input)
        
        if not urls:
            response = "❌ I couldn't find a valid GitHub URL. Please share a link like: https://github.com/username/repo"
        elif not self.current_project:
            response = "⚠️ Please create a project plan first before linking GitHub!"
        else:
            github_url = urls[0]
            self.current_project['github_url'] = github_url
            self.db.save_project(self.current_project)
            
            response = f"✅ **GitHub Linked!**\n\n"
            response += f"Repository: {github_url}\n\n"
            response += f"I'll monitor commits and update task statuses automatically."
        
        ai_msg = AIMessage(content=response)
        self.messages.append(ai_msg)
        return response
    
    def _show_status(self) -> str:
        """Show current project status"""
        if not self.current_project:
            response = "📋 No active project yet. Start by telling me about your project idea!"
        else:
            project = self.current_project
            response = f"📊 **Project Status**\n\n"
            response += f"**{project['title']}**\n"
            response += f"{project['description']}\n\n"
            
            if project.get('github_url'):
                response += f"🔗 GitHub: {project['github_url']}\n\n"
            
            tasks = project.get('tasks', [])
            response += f"**Tasks:** {len(tasks)} total\n"
            
            for task in tasks[:5]:  # Show first 5
                response += f"\n• [{task['status']}] {task['title']}"
            
            if len(tasks) > 5:
                response += f"\n\n...and {len(tasks) - 5} more tasks"
        
        ai_msg = AIMessage(content=response)
        self.messages.append(ai_msg)
        return response
    
    def end_session(self):
        """End session and save to memory"""
        if self.messages:
            session = self.memory.save_session(self.current_project_id, self.messages)
            print(f"\n💾 Session Saved!")
            print(f"Summary: {session['summary']}\n")