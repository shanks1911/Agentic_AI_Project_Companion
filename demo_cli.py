"""
Simple CLI to test the orchestrator
Run: python demo_cli.py
"""
from dotenv import load_dotenv
from src.demo_orchestrator import DemoOrchestrator

load_dotenv()

def main():
    print("=" * 60)
    print("🤖 AI PROJECT ASSISTANT - DEMO")
    print("=" * 60)
    
    app = DemoOrchestrator()
    
    # Show existing projects
    projects = app.db.list_projects()
    if projects:
        print("\n📂 Your Projects:")
        for i, proj in enumerate(projects, 1):
            print(f"   {i}. {proj['title']} (modified: {proj['last_modified'][:10]})")
        print("\nType the number to continue that project, or press Enter for new project.")
        choice = input("Your choice: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(projects):
            selected_project = projects[int(choice) - 1]
            app.start_session(project_id=selected_project['id'])
        else:
            app.start_session()
    else:
        print("\n📂 No existing projects found. Starting fresh!")
        app.start_session()
    
    print("\nCommands:")
    print("  - Type your project idea or questions")
    print("  - Say 'generate plan' when ready")
    print("  - Share GitHub URL to link repo")
    print("  - Say 'status' to see progress")
    print("  - Type 'exit' to quit\n")
    print("=" * 60 + "\n")
    
    while True:
        user_input = input("💬 You: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            app.end_session()
            print("\n👋 Goodbye! Your session has been saved.\n")
            break
        
        if not user_input.strip():
            continue
        
        response = app.chat(user_input)
        print(f"\n🤖 AI:\n{response}\n")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()