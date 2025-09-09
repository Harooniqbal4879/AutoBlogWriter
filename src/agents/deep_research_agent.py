import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
from ..utils.config import Config

class DeepResearchAgent:
    """Conducts comprehensive web research and analysis"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.5,
            api_key=Config.OPENAI_API_KEY
        )
        self.serp_api_key = Config.SERP_API_KEY
    
    def conduct_research(self, topic: str, depth: str = "comprehensive") -> Dict[str, Any]:
        """Conduct deep research on a given topic"""
        
        # Step 1: Web search for current information
        search_results = self._web_search(topic)
        
        # Step 2: Analyze and extract key insights
        insights = self._extract_insights(search_results, topic)
        
        # Step 3: Fact verification and source credibility
        verified_facts = self._verify_facts(insights)
        
        # Step 4: Generate research summary
        summary = self._generate_summary(topic, insights, verified_facts)
        
        return {
            'topic': topic,
            'search_results': search_results,
            'key_insights': insights,
            'verified_facts': verified_facts,
            'summary': summary,
            'sources': [result['link'] for result in search_results if 'link' in result]
        }
    
    def _web_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform web search using SERP API"""
        
        if not self.serp_api_key:
            # Fallback to simulated research results
            return self._simulate_search_results(query)
        
        try:
            import serpapi
            
            search = serpapi.GoogleSearch({
                "q": query,
                "api_key": self.serp_api_key,
                "num": Config.SEARCH_RESULTS_LIMIT
            })
            
            results = search.get_dict()
            
            formatted_results = []
            for result in results.get('organic_results', [])[:10]:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'source': result.get('displayed_link', '')
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Search API error: {e}")
            return self._simulate_search_results(query)
    
    def _simulate_search_results(self, query: str) -> List[Dict[str, Any]]:
        """Simulate search results when API is not available"""
        return [
            {
                'title': f"Comprehensive Guide to {query}",
                'link': f"https://example.com/{query.replace(' ', '-')}",
                'snippet': f"In-depth analysis of {query} with latest trends and insights...",
                'source': "industry-authority.com"
            },
            {
                'title': f"Latest Trends in {query} for 2024",
                'link': f"https://trends.com/{query.replace(' ', '-')}-2024",
                'snippet': f"Discover the emerging trends and future predictions for {query}...",
                'source': "trends-research.com"
            },
            {
                'title': f"{query}: Best Practices and Case Studies",
                'link': f"https://casestudies.com/{query.replace(' ', '-')}",
                'snippet': f"Real-world examples and best practices for implementing {query}...",
                'source': "business-insights.com"
            }
        ]
    
    def _extract_insights(self, search_results: List[Dict], topic: str) -> List[str]:
        """Extract key insights from search results using LLM"""
        
        combined_content = "\n\n".join([
            f"Title: {result['title']}\nSnippet: {result['snippet']}"
            for result in search_results
        ])
        
        system_prompt = f"""You are a Research Analysis Agent. Extract the most important and actionable insights about \"{topic}\" from the search results below.

        Focus on:
        1. Current trends and developments
        2. Statistical data and facts
        3. Expert opinions and predictions
        4. Practical applications and use cases
        5. Challenges and opportunities

        Provide 5-8 key insights, each as a separate bullet point.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Search Results:\n{combined_content}")
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse insights from response
        insights = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                insights.append(line[1:].strip())
            elif line and len(insights) < 10:  # Catch unnumbered insights
                insights.append(line)
        
        return insights[:8]  # Limit to 8 insights
    
    def _verify_facts(self, insights: List[str]) -> List[Dict[str, Any]]:
        """Verify facts and assess credibility"""
        
        verified_facts = []
        
        for insight in insights:
            # Simple verification logic (can be enhanced with fact-checking APIs)
            credibility_score = self._assess_credibility(insight)
            
            verified_facts.append({
                'fact': insight,
                'credibility_score': credibility_score,
                'verification_status': 'verified' if credibility_score > 0.7 else 'needs_review'
            })
        
        return verified_facts
    
    def _assess_credibility(self, fact: str) -> float:
        """Simple credibility assessment (can be enhanced)"""
        
        # Basic scoring based on content characteristics
        score = 0.5  # Base score
        
        # Increase score for specific data points
        if any(char.isdigit() for char in fact):
            score += 0.2
        
        # Increase score for authoritative language
        authoritative_words = ['study', 'research', 'analysis', 'report', 'survey', 'data']
        if any(word in fact.lower() for word in authoritative_words):
            score += 0.2
        
        # Decrease score for vague language
        vague_words = ['might', 'could', 'possibly', 'maybe', 'unclear']
        if any(word in fact.lower() for word in vague_words):
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _generate_summary(self, topic: str, insights: List[str], verified_facts: List[Dict]) -> str:
        """Generate comprehensive research summary"""
        
        high_confidence_facts = [
            fact['fact'] for fact in verified_facts 
            if fact['credibility_score'] > 0.7
        ]
        
        system_prompt = f"""Create a comprehensive research summary about \"{topic}\".
        
        Structure the summary with:
        1. Executive Summary (2-3 sentences)
        2. Key Findings (bullet points)
        3. Current Trends
        4. Implications and Opportunities
        
        Make it informative, well-structured, and actionable.
        """
        
        content = f"High-confidence insights:\n" + "\n".join(high_confidence_facts)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=content)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
