from typing import Dict, Any
from ..utils.config import Config

class ContentStrategistAgent:
    """Formats and organizes research into readable content"""
    def __init__(self):
        from langchain_openai import ChatOpenAI
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError:
            from langchain.schema import HumanMessage, SystemMessage
        self.HumanMessage = HumanMessage
        self.SystemMessage = SystemMessage
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=Config.OPENAI_TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )

    def create_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a senior content strategist. Based on the following research and context, create a detailed content strategy for the topic \"{context.get('topic', '')}\".
        Research Summary: {context.get('research_summary', '')}
        Key Insights: {', '.join(context.get('key_insights', []))}
        Target Audience: {context.get('target_audience', '')}
        Brand Voice: {context.get('brand_voice', '')}
        Please include:
        - Main content themes
        - Suggested formats (blog, video, infographic, etc.)
        - Distribution channels
        - Posting frequency
        - SEO and engagement tips
        - KPIs to track
        """
        messages = [
            self.SystemMessage(content="You are a senior content strategist."),
            self.HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        strategy = response.content
        return {
            "strategy": strategy
        }
