from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import Dict, List
from ..utils.config import Config

class QueryHandlerAgent:
    """Routes requests to appropriate specialized agents"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,  # Lower temperature for routing decisions
            api_key=Config.OPENAI_API_KEY
        )
    
    def analyze_query(self, query: str, conversation_history: List[str] = None) -> Dict[str, any]:
        """Analyze user query and determine routing strategy, using conversation history for context-aware decisions."""
        if conversation_history is None:
            conversation_history = []
        system_prompt = """
        You are a Query Analysis Agent. Your job is to analyze user requests and determine:
        1. What type of content they want (blog, linkedin, research, strategy, image)
        2. What agents should be involved
        3. Whether web research is needed
        4. The target audience and brand voice (if mentioned)
        5. Learn from the user's previous requests and responses (conversation history) to improve routing and personalize agent selection.
        
        Respond with a structured analysis in this format:
        CONTENT_TYPE: [blog/linkedin/research/strategy/image/mixed]
        REQUIRED_AGENTS: [list of agents needed]
        RESEARCH_NEEDED: [yes/no]
        TARGET_AUDIENCE: [if mentioned]
        BRAND_VOICE: [if mentioned]
        INTENT: [brief description of what user wants]
        """
        history_str = "\n".join(conversation_history)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conversation history:\n{history_str}\n\nAnalyze this request: {query}")
        ]
        response = self.llm.invoke(messages)
        # Parse the structured response
        return self._parse_analysis(response.content, query)
    
    def _parse_analysis(self, analysis: str, original_query: str) -> Dict[str, any]:
        """Parse the LLM analysis into structured data"""
        
        lines = analysis.strip().split('\n')
        result = {
            'content_type': 'blog',  # default
            'required_agents': ['research_agent', 'blog_writer'],  # default
            'research_needed': True,  # default
            'target_audience': None,
            'brand_voice': None,
            'intent': original_query,
            'fallback_used': False
        }

        parsed_keys = set()
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                parsed_keys.add(key)

                if 'content_type' in key:
                    result['content_type'] = value.lower()
                elif 'required_agents' in key:
                    # Parse agent list
                    agents = []
                    if 'research' in value.lower():
                        agents.append('research_agent')
                    if 'blog' in value.lower():
                        agents.append('blog_writer')
                    if 'linkedin' in value.lower():
                        agents.append('linkedin_writer')
                    if 'strategy' in value.lower():
                        agents.append('content_strategist')
                    if 'image' in value.lower():
                        agents.append('image_generator')

                    result['required_agents'] = agents or result['required_agents']

                elif 'research_needed' in key:
                    result['research_needed'] = 'yes' in value.lower()
                elif 'target_audience' in key and value.lower() not in ['none', 'not mentioned']:
                    result['target_audience'] = value
                elif 'brand_voice' in key and value.lower() not in ['none', 'not mentioned']:
                    result['brand_voice'] = value
                elif 'intent' in key:
                    result['intent'] = value

        # Always include image_generator for blog, mixed, or image content types
        if result['content_type'] in ['blog', 'mixed', 'image'] and 'image_generator' not in result['required_agents']:
            result['required_agents'].append('image_generator')

        # Fallback routing for ambiguous/unclear requests
        ambiguous = False
        # If required_agents is empty or only contains default, or if content_type is not recognized
        if (not result['required_agents'] or result['required_agents'] == ['research_agent', 'blog_writer'] or
            result['content_type'] not in ['blog', 'linkedin', 'research', 'strategy', 'image', 'mixed'] or
            len(parsed_keys) < 3):
            ambiguous = True

        if ambiguous:
            result['fallback_used'] = True
            result['intent'] = f"Ambiguous or unclear request detected. Fallback routing applied. Original: {original_query}"
            result['content_type'] = 'blog'
            # Always include LinkedInWriterAgent in fallback (PascalCase for orchestrator compatibility)
            result['required_agents'] = ['DeepResearchAgent', 'SEOBlogWriterAgent', 'LinkedInWriterAgent']
            result['research_needed'] = True

        return result
