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
            # Fallback logic: use blog content if topic/research/insights are missing
            blog_content = context.get('blog_content', '')
            topic = context.get('topic', '')
            research_summary = context.get('research_summary', '')
            key_insights = ', '.join(context.get('key_insights', [])) if context.get('key_insights') else ''
            target_audience = context.get('target_audience', '')
            brand_voice = context.get('brand_voice', '')

            # Build a robust prompt
            prompt = """
You are a professional LinkedIn content creator. Your job is to write an engaging LinkedIn post for a professional audience. If a blog post is provided, summarize and adapt it for LinkedIn. If research summary or key insights are available, incorporate them. Always:
- Make the post concise, actionable, and encourage engagement (comments, shares, likes)
- Add relevant hashtags and a call to action
- Use a professional, positive tone
"""
            if topic:
                prompt += f"\nTopic: {topic}"
            if research_summary:
                prompt += f"\nResearch Summary: {research_summary}"
            if key_insights:
                prompt += f"\nKey Insights: {key_insights}"
            if target_audience:
                prompt += f"\nTarget Audience: {target_audience}"
            if brand_voice:
                prompt += f"\nBrand Voice: {brand_voice}"
            if blog_content:
                prompt += f"\nBlog Content: {blog_content}"

            prompt += "\nIf any fields above are missing, use what is available to create a LinkedIn post relevant to the topic."

            messages = [
                self.SystemMessage(content="You are a professional LinkedIn content creator."),
                self.HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            content = response.content[:2000] if response.content else ""
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
