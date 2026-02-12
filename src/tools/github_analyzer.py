"""
GitHub Code Analyzer - NLP-based semantic feature matching
No task ID dependencies - purely semantic comparison
"""
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from github import Github, Auth
import os
import re
import base64
from typing import Dict, List

class GitHubCodeAnalyzer:
    """Analyzes GitHub repository code using semantic understanding"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY"),
            temperature=0.2  # Lower for more consistent analysis
        )
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            auth = Auth.Token(github_token)
            self.github = Github(auth=auth)
        else:
            self.github = Github()
    
    def extract_repo_info(self, github_url: str) -> tuple:
        """Extract owner and repo name from GitHub URL"""
        match = re.match(r'https://github\.com/([\w-]+)/([\w-]+)', github_url)
        if not match:
            raise ValueError("Invalid GitHub URL")
        return match.group(1), match.group(2)
    
    def fetch_all_code_files(self, github_url: str) -> tuple:
        """Fetch ALL code files from repository (no limits)"""
        owner, repo_name = self.extract_repo_info(github_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        code_files = []
        
        # Get all files recursively
        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                # Include all code files
                if self._is_code_file(file_content.path):
                    code_files.append({
                        'path': file_content.path,
                        'size': file_content.size,
                        'content_ref': file_content
                    })
        
        return code_files, repo
    
    def _is_code_file(self, path: str) -> bool:
        """Check if file is a code file"""
        code_extensions = [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs', '.html', '.css',
            '.vue', '.sql', '.sh', '.yaml', '.yml', '.json'
        ]
        
        exclude_patterns = [
            'node_modules', '__pycache__', '.git', 'dist', 'build', 
            '.next', 'venv', '.venv', 'vendor', 'package-lock', 'yarn.lock'
        ]
        
        return (any(path.endswith(ext) for ext in code_extensions) and 
                not any(pattern in path for pattern in exclude_patterns))
    
    def read_file_content(self, repo, file_ref) -> str:
        """Read full content of a file (no character limits)"""
        try:
            if file_ref.encoding == 'base64':
                content = base64.b64decode(file_ref.content).decode('utf-8')
            else:
                content = file_ref.decoded_content.decode('utf-8')
            return content
        except Exception as e:
            return f"[Error reading file: {str(e)}]"
    
    def summarize_codebase(self, github_url: str) -> Dict:
        """
        Comprehensive codebase summarization - reads ALL code files
        Returns detailed feature summary
        """
        print("📂 Fetching repository files...")
        code_files, repo = self.fetch_all_code_files(github_url)
        
        if not code_files:
            return {
                'error': 'No code files found in repository',
                'features': []
            }
        
        print(f"📊 Found {len(code_files)} code files. Analyzing...")
        
        # Group files by directory for better organization
        file_groups = {}
        for file_info in code_files:
            directory = '/'.join(file_info['path'].split('/')[:-1]) or 'root'
            if directory not in file_groups:
                file_groups[directory] = []
            file_groups[directory].append(file_info)
        
        # Analyze each file group
        all_features = []
        
        for directory, files in file_groups.items():
            print(f"  📁 Analyzing {directory}/ ({len(files)} files)...")
            
            # Read all files in this directory
            directory_code = []
            for file_info in files:
                content = self.read_file_content(repo, file_info['content_ref'])
                directory_code.append({
                    'file': file_info['path'],
                    'content': content,
                    'size': len(content)
                })
            
            # Analyze this directory group with LLM
            features = self._analyze_directory_features(directory, directory_code)
            all_features.extend(features)
        
        print(f"✅ Analysis complete. Found {len(all_features)} features.")
        
        return {
            'repository': github_url,
            'total_files': len(code_files),
            'features': all_features,
            'summary': self._create_overall_summary(all_features)
        }
    
    def _analyze_directory_features(self, directory: str, code_files: List[Dict]) -> List[str]:
        """Analyze a group of files to extract implemented features"""
        
        # Prepare code context (chunk if too large)
        code_context = f"Directory: {directory}\n\n"
        
        for file_info in code_files:
            code_context += f"### File: {file_info['file']}\n"
            # Include full content (LLM will handle it)
            code_context += f"```\n{file_info['content']}\n```\n\n"
        
        analysis_prompt = f"""Analyze this code and extract EVERY implemented feature, functionality, and component.

{code_context}

List ALL features you can identify. Be comprehensive and specific. For each feature:
- Describe what it does
- Mention key functions/classes involved
- Note if it's complete or partial

Format as a simple list:
- Feature 1 description
- Feature 2 description
- Feature 3 description

Be thorough - include even small features.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)]).content
            
            # Extract features (lines starting with -)
            features = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    feature = line.lstrip('-•').strip()
                    if feature and len(feature) > 10:  # Filter out noise
                        features.append(feature)
            
            return features
            
        except Exception as e:
            print(f"  ⚠️ Error analyzing {directory}: {e}")
            return []
    
    def _create_overall_summary(self, features: List[str]) -> str:
        """Create high-level summary of all features"""
        if not features:
            return "No features detected in codebase."
        
        summary_prompt = f"""Summarize the following implemented features into a cohesive project description.

Features:
{chr(10).join(f'- {f}' for f in features)}

Provide a 2-3 sentence summary of what this codebase does overall.
"""
        
        try:
            summary = self.llm.invoke([HumanMessage(content=summary_prompt)]).content
            return summary.strip()
        except:
            return "Multiple features implemented across the codebase."
    
    def match_features_to_tasks(self, implemented_features: List[str], tasks: List[Dict]) -> List[Dict]:
        """
        Semantic matching of implemented features to task descriptions
        No task IDs needed - pure NLP matching
        """
        
        if not implemented_features or not tasks:
            return []
        
        # Prepare matching prompt
        features_text = '\n'.join(f"{i+1}. {feature}" for i, feature in enumerate(implemented_features))
        
        tasks_text = '\n'.join(
            f"Task: {task.get('title', 'Untitled')}\nDescription: {task.get('description', '')}\nCurrent Status: {task.get('status', 'To-Do')}\n"
            for task in tasks
        )
        
        matching_prompt = f"""You are analyzing whether tasks have been implemented based on actual code features.

IMPLEMENTED FEATURES IN CODE:
{features_text}

PROJECT TASKS:
{tasks_text}

For EACH task, determine:
1. Is this task implemented? (Yes/No/Partial)
2. Which code features prove it?
3. Confidence level (High/Medium/Low)
4. Suggested new status (Completed/In Progress/Not Started)

Respond in this format for EVERY task:

TASK_TITLE: [exact task title]
IMPLEMENTED: [Yes/No/Partial]
EVIDENCE: [which features from the code prove this]
CONFIDENCE: [High/Medium/Low]
NEW_STATUS: [Completed/In Progress/Not Started]

Analyze ALL tasks. Be strict - only mark as Completed if clear evidence exists.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=matching_prompt)]).content
            
            # Parse response
            matches = self._parse_matching_results(response, tasks)
            
            return matches
            
        except Exception as e:
            print(f"Error in matching: {e}")
            return []
    
    def _parse_matching_results(self, llm_response: str, tasks: List[Dict]) -> List[Dict]:
        """Parse LLM matching results"""
        results = []
        
        lines = llm_response.split('\n')
        current_match = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TASK_TITLE:'):
                if current_match:
                    results.append(current_match)
                
                title = ':'.join(line.split(':')[1:]).strip()
                # Find matching task
                matched_task = None
                for task in tasks:
                    if self._titles_match(title, task.get('title', '')):
                        matched_task = task
                        break
                
                current_match = {
                    'task': matched_task,
                    'task_title': title,
                    'implemented': 'No',
                    'evidence': '',
                    'confidence': 'Low',
                    'new_status': 'Not Started'
                }
            
            elif line.startswith('IMPLEMENTED:') and current_match:
                current_match['implemented'] = line.split(':')[1].strip()
            
            elif line.startswith('EVIDENCE:') and current_match:
                current_match['evidence'] = ':'.join(line.split(':')[1:]).strip()
            
            elif line.startswith('CONFIDENCE:') and current_match:
                current_match['confidence'] = line.split(':')[1].strip()
            
            elif line.startswith('NEW_STATUS:') and current_match:
                current_match['new_status'] = line.split(':')[1].strip()
        
        # Add last match
        if current_match:
            results.append(current_match)
        
        return results
    
    def _titles_match(self, title1: str, title2: str) -> bool:
        """Fuzzy title matching"""
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        # Exact match
        if t1 == t2:
            return True
        
        # Substring match
        if t1 in t2 or t2 in t1:
            return True
        
        # Word overlap (>50% of words match)
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        min_length = min(len(words1), len(words2))
        
        return overlap / min_length > 0.5


# Lazy loading
analyzer = None

def get_analyzer():
    """Lazy load analyzer"""
    global analyzer
    if analyzer is None:
        analyzer = GitHubCodeAnalyzer()
    return analyzer


@tool
def analyze_github_code_comprehensively_tool(github_url: str) -> str:
    """
    Comprehensively analyze ALL code in a GitHub repository.
    Reads every code file and summarizes implemented features.
    No limits - analyzes the entire codebase.
    
    Args:
        github_url: The GitHub repository URL
    
    Returns:
        Detailed summary of all implemented features
    """
    try:
        a = get_analyzer()
        
        result_dict = a.summarize_codebase(github_url)
        
        if 'error' in result_dict:
            return f"❌ Error: {result_dict['error']}"
        
        result = f"📊 **Comprehensive Code Analysis**\n\n"
        result += f"Repository: {github_url}\n"
        result += f"Files Analyzed: {result_dict['total_files']}\n"
        result += f"Features Found: {len(result_dict['features'])}\n\n"
        
        result += f"**Overall Summary:**\n{result_dict['summary']}\n\n"
        
        result += f"**Implemented Features:**\n"
        for i, feature in enumerate(result_dict['features'], 1):
            result += f"{i}. {feature}\n"
        
        return result
        
    except Exception as e:
        return f"Error analyzing repository: {str(e)}"


@tool
def match_code_to_tasks_semantic_tool(github_url: str) -> str:
    """
    Analyze GitHub code and semantically match it to project tasks.
    Does NOT require task IDs - uses pure NLP semantic matching.
    Updates task statuses based on what's actually implemented in code.
    
    Args:
        github_url: The GitHub repository URL
    
    Returns:
        Task status updates with evidence from code
    """
    # This will be handled in the orchestrator with direct access to tasks
    return "SEMANTIC_MATCHING_REQUESTED"


# Keep old tools for backward compatibility but mark as deprecated
@tool
def analyze_github_repository_tool(github_url: str) -> str:
    """Deprecated - use analyze_github_code_comprehensively_tool instead"""
    return analyze_github_code_comprehensively_tool.invoke({'github_url': github_url})


@tool
def match_code_to_tasks_tool(github_url: str) -> str:
    """Deprecated - use match_code_to_tasks_semantic_tool instead"""
    return match_code_to_tasks_semantic_tool.invoke({'github_url': github_url})