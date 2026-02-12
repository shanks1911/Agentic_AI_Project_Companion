from dotenv import load_dotenv

from agents.generate_plan import generate_project_plan

def main():
    """
    This is the main function that orchestrates the agent's run.
    """
    # 1. Setup: Load the GOOGLE_API_KEY from your .env file
    load_dotenv()
    
    # 2. User Interaction: Get the project idea from the user
    user_idea = input("What is your project idea? ")
    
    # A small check to make sure the user actually typed something
    if not user_idea.strip():
        print("No input received. Exiting.")
        return
        
    # 3. Call the Agent: Pass the user's idea to your core logic function
    final_plan = generate_project_plan(user_idea)
    
    # 4. Present the Output: Print the result in a clean, readable format
    print("\n--- ✅ Success! Here is your project plan: ---")
    print(f"\nTitle: {final_plan.project_title}")
    print(f"Description: {final_plan.project_description}")
    print("\nInitial Tasks (To-Do):")
    for task in final_plan.tasks:
        print(f"  - ({task.id}) {task.title}: {task.description}")
    print("\n-------------------------------------------------")

if __name__ == "__main__":
    main()