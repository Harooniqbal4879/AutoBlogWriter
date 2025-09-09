import unittest
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)
from src.orchestrator.workflow_orchestrator import ContentMarketingOrchestrator
from src.orchestrator.state import ContentMarketingState

class TestInterAgentCommunication(unittest.TestCase):
    def test_context_preservation(self):
        orchestrator = ContentMarketingOrchestrator()
        initial_state = ContentMarketingState(
            user_query="Write a blog post about AI in marketing.",
            conversation_history=[],
            content_type="blog",
            target_audience="Marketing Professionals",
            brand_voice="Professional",
            query_intent="Inform and engage",
            required_agents=["DeepResearchAgent", "SEOBlogWriterAgent", "LinkedInWriterAgent"],
            research_needed=True,
            research_results=[],
            web_sources=[],
            key_insights=[],
            facts_and_stats=[],
            blog_content=None,
            linkedin_content=None,
            research_summary=None,
            strategy_content=None,
            image_prompts=[],
            generated_images=[],
            keywords=[],
            seo_score=None,
            readability_score=None,
            content_quality_scores={},
            fact_check_results=[],
            processing_steps=[],
            errors=[],
            warnings=[],
            success=False,
            current_step="",
            next_steps=[],
            completed_agents=[],
            linkedin_ids="",
            auth_codes="",
            urls=""
        )
        result = orchestrator.app.invoke(initial_state, config={"thread_id": "test-thread"})
        # Check that research results are used in blog and LinkedIn content
        self.assertTrue(result.get("research_summary"))
        self.assertTrue(result.get("blog_content"))
        self.assertTrue(result.get("linkedin_content"))
        self.assertIn("AI", result.get("blog_content", ""))
        self.assertIn("AI", result.get("linkedin_content", ""))
        print("Research Summary:", result.get("research_summary"))
        print("Blog Content:", result.get("blog_content"))
        print("LinkedIn Content:", result.get("linkedin_content"))

if __name__ == "__main__":
    unittest.main()
