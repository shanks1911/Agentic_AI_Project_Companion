# -*- coding: utf-8 -*-


"""
Agentic CLI - Agent decides what to do autonomously
Run: python demo_agentic_cli.py
"""
print(" CLI started")


from dotenv import load_dotenv
from src.agentic_orchestrator import AgenticOrchestrator

load_dotenv()

def main():
    print("=" * 60)
    print("🤖 AGENTIC AI PROJECT ASSISTANT")
    print("=" * 60)
    print("\n✨ The agent will autonomously decide which tools to use\n")
    
    app = AgenticOrchestrator()
    
    # Show existing projects
    projects = app.db.list_projects()
    if projects:
        print("📂 Your Projects:")
        for i, proj in enumerate(projects, 1):
            print(f"   {i}. {proj['title']}")
        print("\nType number to continue project, or press Enter for new:")
        choice = input("Your choice: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(projects):
            selected = projects[int(choice) - 1]
            app.start_session(project_id=selected['id'])
        else:
            app.start_session()
    else:
        print("📂 No existing projects. Starting fresh!\n")
        app.start_session()
    
    print("\n💡 Tips:")
    print("  - Describe your project idea")
    print("  - The agent will ask questions to refine it")
    print("  - Agent will automatically create a plan when ready")
    print("  - Paste GitHub URLs to link repositories")
    print("  - Type 'exit' to quit\n")
    print("=" * 60 + "\n")
    
    while True:
        user_input = input("💬 You: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            app.end_session()
            print("\n👋 Goodbye!\n")
            break
        
        if not user_input.strip():
            continue
        
        try:
            response = app.chat(user_input)
            print(f"\n🤖 AI:\n{response}\n")
            print("-" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("Please try again.\n")

if __name__ == "__main__":
    main()