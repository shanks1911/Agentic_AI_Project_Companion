# Agentic AI Project Companionship: A Multi-Agent Adaptive Framework for Cognitive Collaboration in Project Management

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20manager-poetry-blue)](https://python-poetry.org/)
[![LangGraph](https://img.shields.io/badge/framework-LangGraph-green)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange)](https://ai.google.dev/)

This is an advanced, conversational AI assistant designed to help users plan, manage, and execute their professional and personal projects. It leverages a hierarchical, stateful agentic system built with LangGraph and powered by Google's Gemini models to provide an interactive and intelligent project management experience.

## [Click Here to Watch Demo](https://drive.google.com/file/d/13qSjjlHHJ6IZ7KwU8Q-gLW0UtlCv6j3B/view?usp=drive_link)

# ✨ Key Features

## 🧠 Multi-Agent Architecture

Specialized AI agents work collaboratively:

### 🎯 Orchestrator Agent
- Coordinates the complete workflow
- Routes user requests to specialized agents
- Maintains global application state
- Controls execution flow between agents

### 💡 Idea Agent
- Helps users refine vague project ideas
- Generates feature suggestions and improvements
- Clarifies requirements through conversation
- Assists in brainstorming and ideation

### 📋 Planner Agent
- Converts refined ideas into structured execution plans
- Generates Kanban-style task workflows
- Generates realistic gantt-chart based on user given deadline
- Generates a sequence diagram for the project
- Creates milestones, priorities, and dependencies
- Organizes projects into actionable steps

### 🔍 Research Agent
- Performs intelligent topic research
- Collects contextual information for projects
- Searches through arxiv and semantic scholar repositories
- Enhances plans using external knowledge
- Supports technical and career-related exploration

### 🐙 GitHub Agent
- Assists with repository-related workflows
- Helps generate development-oriented structures
- Supports code/project organization
- Enables future GitHub integration capabilities

---


# 💬 Conversational AI Experience

- Natural language interaction with persistent memory
- Context-aware conversations across sessions using rolling summaries
- Dynamic response generation using Gemini models
- Continuous refinement of project plans through dialogue

---

# 📂 Intelligent Project Planning

Generate detailed and structured project plans automatically:
- Task breakdown generation
- Priority assignment
- Milestone creation
- Workflow organization
- Kanban-style project management

---

# ✏️ Interactive Plan Modification

Modify projects through simple conversation:
- Add new tasks
- Edit task descriptions
- Change priorities and statuses
- Reorganize workflows
- Expand existing plans dynamically

---

# 💾 Persistent Memory & State Management

- Stateful conversation architecture using LangGraph
- Save project plans as JSON files
- Resume previous sessions seamlessly
- Context preservation across workflows

---

## 🛠️ Architecture Overview

This Project is built around a sophisticated stateful agent system using LangGraph:

<img width="599" height="329" alt="Architecture Diagram drawio" src="https://github.com/user-attachments/assets/e150ff6e-a746-41f9-b9e3-c5ba845c5d52" />



## 💻 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.12+ | Core application runtime |
| **Dependency Management** | Poetry | Package and environment management |
| **Agent Framework** | LangGraph | State-based agent orchestration |
| **LLM Provider** | Google Gemini | Natural language processing |
| **Database** | MongoDB | Stores project details, sessions, contexts and similarity search |
| **Environment Config** | python-dotenv | Environment variable management |

## 🚀 Getting Started

### Prerequisites
- Python 3.12 or higher
- Poetry (for dependency management)
- MongoURI
- Github Token
- Google AI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/careerforge.git
   cd agentic
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google AI API key
   GEMINI_KEY=your_google_ai_api_key_here
   ```

4. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

### Usage

Start the interactive session:
```bash
python -m src.main_agent
```



## 🔧 Configuration

### Environment Variables
```bash
GEMINI_KEY=your_google_ai_api_key_here
MONGO_URI=your_mongodb_uri_here
GITHUB_TOKEN=your_github_token_here
```


## 🎯 Use Cases

- **Software Development Projects**: Break down app ideas into actionable development tasks
- **Career Planning**: Create structured plans for skill development and career transitions
- **Personal Projects**: Organize creative projects, learning goals, or home improvements
- **Business Planning**: Structure startup ideas or business process improvements
- **Research Projects**: Plan academic or professional research initiatives

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) for the agent framework
- [Google AI](https://ai.google.dev/) for the Gemini models
- The open-source community for inspiration and tools

**Happy Planning! 🚀**
