"""
Research Paper Agent - Searches academic papers and generates literature reviews
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
import os
import requests
from typing import List, Dict
import json

class ResearchPaperAgent:
    """Agent for academic paper research and citation management"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_KEY")
        )
        self.arxiv_base = "http://export.arxiv.org/api/query"
        self.semantic_base = "https://api.semanticscholar.org/graph/v1"
    
    def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search ArXiv for academic papers"""
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(self.arxiv_base, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = {
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                    'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                               for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                    'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()[:500],
                    'published': entry.find('{http://www.w3.org/2005/Atom}published').text[:10],
                    'link': entry.find('{http://www.w3.org/2005/Atom}id').text,
                    'source': 'ArXiv'
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"ArXiv search error: {e}")
            return []
    
    def search_semantic_scholar(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Semantic Scholar for academic papers"""
        try:
            url = f"{self.semantic_base}/paper/search"
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'title,authors,year,abstract,citationCount,url'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper in data.get('data', []):
                papers.append({
                    'title': paper.get('title', 'Unknown'),
                    'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])],
                    'summary': paper.get('abstract', 'No abstract available')[:500],
                    'published': str(paper.get('year', 'Unknown')),
                    'citations': paper.get('citationCount', 0),
                    'link': paper.get('url', ''),
                    'source': 'Semantic Scholar'
                })
            
            return papers
            
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []
    
    def rank_papers_by_relevance(self, papers: List[Dict], project_description: str) -> List[Dict]:
        """Use LLM to rank papers by relevance to project"""
        if not papers:
            return []
        
        # Create paper summaries
        paper_summaries = []
        for i, paper in enumerate(papers):
            summary = f"{i+1}. {paper['title']} ({paper['published']})\n"
            summary += f"   Authors: {', '.join(paper['authors'][:3])}\n"
            summary += f"   {paper['summary'][:200]}...\n"
            paper_summaries.append(summary)
        
        ranking_prompt = f"""You are a research paper ranking expert. Rank these papers by relevance to the given project.

PROJECT: {project_description}

PAPERS:
{''.join(paper_summaries)}

For each paper, assign a relevance score from 0.0 to 1.0 where:
- 1.0 = Highly relevant, directly addresses the project
- 0.7-0.9 = Very relevant, addresses similar problems
- 0.4-0.6 = Somewhat relevant, related topic
- 0.0-0.3 = Not relevant

Respond in this format:
PAPER_ID: 1
SCORE: 0.85
REASON: [brief reason]

PAPER_ID: 2
SCORE: 0.92
REASON: [brief reason]
"""
        
        response = self.llm.invoke([HumanMessage(content=ranking_prompt)]).content
        
        # Parse rankings
        rankings = {}
        lines = response.split('\n')
        current_paper = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('PAPER_ID:'):
                current_paper = int(line.split(':')[1].strip())
                rankings[current_paper] = {'score': 0.0, 'reason': ''}
            elif line.startswith('SCORE:') and current_paper:
                try:
                    score = float(line.split(':')[1].strip())
                    rankings[current_paper]['score'] = score
                except ValueError:
                    rankings[current_paper]['score'] = 0.5
            elif line.startswith('REASON:') and current_paper:
                reason = ':'.join(line.split(':')[1:]).strip()
                rankings[current_paper]['reason'] = reason
        
        # Apply rankings to papers
        for i, paper in enumerate(papers):
            paper_id = i + 1
            if paper_id in rankings:
                paper['relevance_score'] = rankings[paper_id]['score']
                paper['relevance_reason'] = rankings[paper_id]['reason']
            else:
                paper['relevance_score'] = 0.5
                paper['relevance_reason'] = 'Not ranked'
        
        # Sort by relevance
        papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return papers
    
    def generate_literature_review(self, papers: List[Dict], project_description: str) -> str:
        """Generate a literature review based on relevant papers"""
        if not papers:
            return "No papers found for literature review."
        
        # Use top 5 most relevant papers
        top_papers = papers[:5]
        
        paper_details = []
        for paper in top_papers:
            detail = f"- **{paper['title']}** ({paper['published']})\n"
            detail += f"  Authors: {', '.join(paper['authors'][:3])}\n"
            detail += f"  Summary: {paper['summary']}\n"
            detail += f"  Relevance: {paper.get('relevance_score', 0.5):.2f} - {paper.get('relevance_reason', '')}\n"
            paper_details.append(detail)
        
        review_prompt = f"""Generate a professional literature review for an academic paper.

PROJECT: {project_description}

RELEVANT PAPERS:
{''.join(paper_details)}

Write a comprehensive literature review that:
1. Introduces the research area
2. Discusses each paper's contribution
3. Identifies gaps in existing research
4. Explains how this project addresses those gaps

Format as academic prose with proper citations [Author et al., Year].
"""
        
        review = self.llm.invoke([HumanMessage(content=review_prompt)]).content
        
        return review
    
    def generate_citations(self, papers: List[Dict], style: str = "APA") -> str:
        """Generate formatted citations"""
        citations = []
        
        for paper in papers:
            if style == "APA":
                authors = paper['authors'][:3]
                author_str = ', '.join(authors)
                if len(paper['authors']) > 3:
                    author_str += ', et al.'
                
                citation = f"{author_str} ({paper['published']}). {paper['title']}. "
                citation += f"Retrieved from {paper['link']}"
                
            elif style == "IEEE":
                authors = paper['authors'][:3]
                author_str = ', '.join([name.split()[-1] for name in authors])
                citation = f"[{len(citations)+1}] {author_str}, \"{paper['title']},\" {paper['published']}."
            
            else:  # MLA
                first_author = paper['authors'][0] if paper['authors'] else "Unknown"
                last_name = first_author.split()[-1]
                citation = f"{last_name}, et al. \"{paper['title']}.\" {paper['published']}."
            
            citations.append(citation)
        
        return '\n'.join(citations)


# Create research tools
research_agent = None

def get_research_agent():
    """Lazy load research agent"""
    global research_agent
    if research_agent is None:
        research_agent = ResearchPaperAgent()
    return research_agent


@tool
def search_research_papers_tool(query: str, max_results: int = 10) -> str:
    """
    Search academic papers from ArXiv and Semantic Scholar.
    Use this to find related research for literature reviews.
    
    Args:
        query: Search query (keywords about the research topic)
        max_results: Maximum number of papers to return (default 10)
    
    Returns:
        List of relevant academic papers with titles, authors, and summaries
    """
    agent = get_research_agent()
    
    # Search both sources
    arxiv_papers = agent.search_arxiv(query, max_results//2)
    semantic_papers = agent.search_semantic_scholar(query, max_results//2)
    
    all_papers = arxiv_papers + semantic_papers
    
    if not all_papers:
        return f"No papers found for query: {query}"
    
    # Format results
    result = f"📚 Found {len(all_papers)} research papers for '{query}'\n\n"
    
    for i, paper in enumerate(all_papers[:max_results], 1):
        result += f"{i}. **{paper['title']}**\n"
        result += f"   Authors: {', '.join(paper['authors'][:3])}\n"
        result += f"   Published: {paper['published']}\n"
        if 'citations' in paper:
            result += f"   Citations: {paper['citations']}\n"
        result += f"   Source: {paper['source']}\n"
        result += f"   {paper['summary'][:150]}...\n\n"
    
    return result


@tool
def generate_literature_review_tool(query: str, project_description: str) -> str:
    """
    Generate a comprehensive literature review based on research papers.
    Use this to create the literature review section of a research paper.
    
    Args:
        query: Search query for papers
        project_description: Description of your project/research
    
    Returns:
        Formatted literature review with citations
    """
    agent = get_research_agent()
    
    # Search papers
    arxiv_papers = agent.search_arxiv(query, 10)
    semantic_papers = agent.search_semantic_scholar(query, 10)
    all_papers = arxiv_papers + semantic_papers
    
    if not all_papers:
        return "No papers found to generate literature review."
    
    # Rank by relevance
    ranked_papers = agent.rank_papers_by_relevance(all_papers, project_description)
    
    # Generate review
    review = agent.generate_literature_review(ranked_papers, project_description)
    
    # Add citations
    citations = agent.generate_citations(ranked_papers[:10], style="APA")
    
    result = "# Literature Review\n\n"
    result += review
    result += "\n\n## References\n\n"
    result += citations
    
    return result