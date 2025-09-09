from typing import Dict, Any
from ..utils.config import Config

class LinkedInWriterAgent:
    """Generates engaging professional LinkedIn content"""
    def __init__(self):
        self._cache = {}
        import os
        provider = os.getenv("LLM_PROVIDER", "OpenAI GPT-4")
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError:
            from langchain.schema import HumanMessage, SystemMessage
        self.HumanMessage = HumanMessage
        self.SystemMessage = SystemMessage
        if provider == "OpenAI GPT-4":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=Config.OPENAI_MODEL,
                temperature=Config.OPENAI_TEMPERATURE,
                api_key=os.getenv("OPENAI_API_KEY", Config.OPENAI_API_KEY)
            )
        elif provider == "Perplexity Sonar":
            from langchain_perplexity import ChatPerplexity
            self.llm = ChatPerplexity(
                model="sonar-large-online",
                temperature=Config.OPENAI_TEMPERATURE,
                api_key=os.getenv("PERPLEXITY_API_KEY", "")
            )
        elif provider == "Claude Sonnet":
            from langchain_anthropic import ChatAnthropic
            self.llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=Config.OPENAI_TEMPERATURE,
                api_key=os.getenv("CLAUDE_API_KEY", "")
            )
        elif provider == "Google Gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=Config.OPENAI_TEMPERATURE,
                api_key=os.getenv("GEMINI_API_KEY", "")
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def create_linkedin_post(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Create a hashable cache key from context
        import hashlib, json
        cache_key = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        try:
            prompt = f"""
            You are a professional LinkedIn content creator. Write an engaging LinkedIn post about \"{context.get('topic', '')}\" for the following audience:
            Research Summary: {context.get('research_summary', '')}
            Key Insights: {', '.join(context.get('key_insights', []))}
            Target Audience: {context.get('target_audience', '')}
            Brand Voice: {context.get('brand_voice', '')}
            The post should be concise, actionable, and encourage engagement (comments, shares, likes). Add relevant hashtags and a call to action.
            """
            messages = [
                self.SystemMessage(content="You are a professional LinkedIn content creator."),
                self.HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            content = response.content
            quality_score = 88
            result = {
                "content": content,
                "quality_score": quality_score
            }
            self._cache[cache_key] = result
            return result
        except Exception as e:
            error_msg = str(e)
            if "key" in error_msg.lower() or "token" in error_msg.lower():
                result = {
                    "error": "API key missing or invalid. Please check your credentials.",
                    "content": "",
                    "quality_score": 0
                }
                self._cache[cache_key] = result
                return result
            result = {
                "error": f"An error occurred: {error_msg}",
                "content": "",
                "quality_score": 0
            }
            self._cache[cache_key] = result
            return result
