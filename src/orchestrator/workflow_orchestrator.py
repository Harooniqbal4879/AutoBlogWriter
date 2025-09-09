from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any
import json

from ..agents.query_handler_agent import QueryHandlerAgent
from ..agents.deep_research_agent import DeepResearchAgent
# from ..agents.blog_writer import SEOBlogWriterAgent
# from ..agents.linkedin_writer import LinkedInWriterAgent
# from ..agents.image_generator import ImageGenerationAgent
# from ..agents.content_strategist import ContentStrategistAgent
from .state import ContentMarketingState


class ContentMarketingOrchestrator:
    """Main orchestrator using LangGraph for intelligent content creation workflow"""

    def __init__(self):
        # Initialize all agents
        self.query_handler = QueryHandlerAgent()
        self.research_agent = DeepResearchAgent()
        
        # Import and initialize other agents
        from ..agents.blog_writer_agent import SEOBlogWriterAgent
        from ..agents.image_generation_agent import ImageGenerationAgent
        from ..agents.linkedin_writer_agent import LinkedInWriterAgent
        
        self.blog_writer = SEOBlogWriterAgent()
        self.image_generator = ImageGenerationAgent()
        self.linkedin_writer = LinkedInWriterAgent()
        
        # Build the workflow
        self.workflow = self._build_workflow()
        # Compile with memory
        self.app = self.workflow.compile(checkpointer=MemorySaver())

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ContentMarketingState)
        
        # Add nodes
        workflow.add_node("query_analysis", self._query_analysis_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("blog_writing", self._blog_writing_node)
        workflow.add_node("image_generation", self._image_generation_node)
        workflow.add_node("linkedin_writing", self._linkedin_writing_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("query_analysis")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "query_analysis",
            self._route_after_query_analysis,
            {"research": "research"}
        )
        workflow.add_conditional_edges(
            "research",
            self._route_after_research,
            {"blog": "blog_writing", "finalize": "finalize"}
        )
        workflow.add_conditional_edges(
            "blog_writing",
            self._route_after_blog,
            {"images": "image_generation", "linkedin": "linkedin_writing", "finalize": "finalize"}
        )
        workflow.add_conditional_edges(
            "linkedin_writing",
            self._route_after_linkedin,
            {"finalize": "finalize"}
        )
        workflow.add_conditional_edges(
            "image_generation",
            self._route_after_images,
            {"finalize": "finalize"}
        )
        workflow.add_edge("finalize", END)
        
        return workflow

    def _query_analysis_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Analyze the user query to determine workflow requirements"""
        print("🔍 Analyzing query...")
        query_result = self.query_handler.analyze_query({
            "query": state["user_query"],
            "conversation_history": state.get("conversation_history", [])
        })
        
        return {
            **state,
            "query_intent": query_result.get("intent", ""),
            "content_type": query_result.get("content_type", "blog"),
            "target_audience": query_result.get("target_audience", ""),
            "brand_voice": query_result.get("brand_voice", ""),
            "required_agents": query_result.get("required_agents", []),
            "research_needed": query_result.get("research_needed", True),
            "current_step": "query_analysis",
            "processing_steps": state.get("processing_steps", []) + ["Query Analysis Complete"],
            "completed_agents": state.get("completed_agents", []) + ["query_handler_agent"]
        }

    def _research_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Perform deep research on the topic"""
        print("🔬 Conducting research...")
        research_result = self.research_agent.conduct_research(
            topic=state["user_query"],
            depth="comprehensive"
        )
        return {
            **state,
            "research_results": research_result.get("search_results", []),
            "web_sources": research_result.get("sources", []),
            "key_insights": research_result.get("key_insights", []),
            "facts_and_stats": research_result.get("verified_facts", []),
            "research_summary": research_result.get("summary", ""),
            "keywords": [],
            "current_step": "research",
            "processing_steps": state.get("processing_steps", []) + ["Research Complete"],
            "completed_agents": state.get("completed_agents", []) + ["deep_research_agent"]
        }

    def _blog_writing_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Generate blog content"""
        print("✍️ Generating blog content...")
        blog_result = self.blog_writer.create_blog_post({
            "topic": state["user_query"],
            "research_summary": state.get("research_summary", ""),
            "key_insights": state.get("key_insights", []),
            "target_audience": state.get("target_audience", ""),
            "brand_voice": state.get("brand_voice", "")
        })
        
        return {
            **state,
            "blog_content": blog_result.get("content", ""),
            "keywords": blog_result.get("keywords", []),
            "seo_score": blog_result.get("seo_score", None),
            "readability_score": blog_result.get("readability_score", None),
            "content_quality_scores": {"blog": blog_result.get("quality_score", None)},
            "current_step": "blog_writing",
            "processing_steps": state.get("processing_steps", []) + ["Blog Writing Complete"],
            "completed_agents": state.get("completed_agents", []) + ["blog_writer_agent"]
        }

    def _image_generation_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Generate images for the content"""
        print("🖼️ Generating images...")
        image_result = self.image_generator.generate_images({
            "topic": state["user_query"],
            "research_summary": state.get("research_summary", ""),
            "target_audience": state.get("target_audience", ""),
            "brand_voice": state.get("brand_voice", "")
        })
        
        return {
            **state,
            "image_prompts": image_result.get("prompts", []),
            "generated_images": image_result.get("images", []),
            "current_step": "image_generation",
            "processing_steps": state.get("processing_steps", []) + ["Image Generation Complete"],
            "completed_agents": state.get("completed_agents", []) + ["image_generation_agent"]
        }

    def _linkedin_writing_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Generate LinkedIn content"""
        print("🔗 Generating LinkedIn content...")
        linkedin_result = self.linkedin_writer.create_linkedin_post({
            "topic": state["user_query"],
            "research_summary": state.get("research_summary", ""),
            "key_insights": state.get("key_insights", []),
            "target_audience": state.get("target_audience", ""),
            "brand_voice": state.get("brand_voice", "")
        })
        
        return {
            **state,
            "linkedin_content": linkedin_result.get("content", ""),
            "content_quality_scores": {
                **state.get("content_quality_scores", {}), 
                "linkedin": linkedin_result.get("quality_score", None)
            },
            "current_step": "linkedin_writing",
            "processing_steps": state.get("processing_steps", []) + ["LinkedIn Writing Complete"],
            "completed_agents": state.get("completed_agents", []) + ["linkedin_writer_agent"]
        }

    def _finalize_node(self, state: ContentMarketingState) -> ContentMarketingState:
        """Finalize the workflow and prepare final output"""
        print("✅ Finalizing workflow...")
        return {
            **state,
            "current_step": "finalize",
            "success": True,
            "processing_steps": state.get("processing_steps", []) + ["Workflow Complete"],
            "next_steps": []
        }

    # Routing logic
    def _route_after_query_analysis(self, state: ContentMarketingState) -> str:
        """Route after query analysis based on requirements"""
        if state.get("research_needed", True):
            return "research"
        # Direct routing for other content types could be added here
        # if state.get("content_type") == "blog":
        #     return "blog_direct"
        # elif state.get("content_type") == "linkedin":
        #     return "linkedin_direct"
        # elif state.get("content_type") == "strategy":
        #     return "strategy_direct"
        return "research"
    
    def _route_after_research(self, state: ContentMarketingState) -> str:
        """Route after research based on content type"""
        if state.get("content_type") == "blog":
            return "blog"
        return "finalize"

    def _route_after_blog(self, state: ContentMarketingState) -> str:
        """Route after blog writing - to image generation, LinkedIn, or finalize"""
        # If LinkedIn content is required, route to LinkedIn writing
        if "LinkedInWriterAgent" in state.get("required_agents", []):
            return "linkedin"
        return "images"

    def _route_after_linkedin(self, state: ContentMarketingState) -> str:
        """Route after LinkedIn writing - typically to finalize"""
        return "finalize"

    def _route_after_images(self, state: ContentMarketingState) -> str:
        """Route after image generation - typically to finalize"""
        return "finalize"