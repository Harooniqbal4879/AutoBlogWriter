from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class ContentMarketingState(TypedDict):
    """State object that flows through the LangGraph workflow"""
    
    # Input
    user_query: str
    conversation_history: List[BaseMessage]
    content_type: str  # "blog", "linkedin", "research", "strategy", "image"
    target_audience: Optional[str]
    brand_voice: Optional[str]
    
    # Query Analysis
    query_intent: str
    required_agents: List[str]
    research_needed: bool
    
    # Research Data
    research_results: List[Dict[str, Any]]
    web_sources: List[str]
    key_insights: List[str]
    facts_and_stats: List[str]
    
    # Content Generation
    blog_content: Optional[str]
    linkedin_content: Optional[str]
    research_summary: Optional[str]
    strategy_content: Optional[str]
    
    # Image Generation
    image_prompts: List[str]
    generated_images: List[str]
    
    # SEO and Optimization
    keywords: List[str]
    seo_score: Optional[int]
    readability_score: Optional[float]
    
    # Quality Control
    content_quality_scores: Dict[str, int]
    fact_check_results: List[Dict[str, Any]]
    
    # Metadata
    processing_steps: List[str]
    errors: List[str]
    warnings: List[str]
    success: bool
    
    # Flow Control
    current_step: str
    next_steps: List[str]
    completed_agents: List[str]
