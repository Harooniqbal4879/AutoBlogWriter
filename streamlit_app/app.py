
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from src.orchestrator.workflow_orchestrator import ContentMarketingOrchestrator
from src.orchestrator.state import ContentMarketingState
import uuid

# Configure the page - must be the first Streamlit command
st.set_page_config(
    page_title="AutoBlogWriter", 
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded"
)

st.title("AutoBlogWriter: Intelligent Content Creation")

# Sidebar navigation for settings


st.sidebar.title("Settings & Authentication")
llm_provider = st.sidebar.selectbox(
    "LLM Provider",
    ["OpenAI", "Claude", "Gemini", "Perplexity", "Tavily"],
    index=0
)
# Dynamic API key label based on provider
api_key_labels = {
    "OpenAI": "OpenAI API Key",
    "Claude": "Anthropic API Key",
    "Gemini": "Google Gemini API Key",
    "Perplexity": "Perplexity API Key",
    "Tavily": "Tavily API Key"
}
api_key_label = api_key_labels.get(llm_provider, "API Key")
openai_api_key = st.sidebar.text_input(api_key_label, value="", type="password")
linkedin_ids = st.sidebar.text_area("LinkedIn IDs (comma separated)", value="")
auth_codes = st.sidebar.text_area("Authentication Codes", value="")
urls = st.sidebar.text_area("URLs (comma separated)", value="")

# Main content input
user_query = st.text_area("Enter your content request:", "Write a blog post about AI in marketing.")

if st.button("Generate Content"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    else:
        try:
            # Set environment variable
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
            # Show progress
            with st.spinner("Generating content..."):
                # Initialize orchestrator
                orchestrator = ContentMarketingOrchestrator()
                
                # Create initial state
                initial_state = ContentMarketingState(
                    user_query=user_query,
                    conversation_history=[],
                    content_type="blog",
                    target_audience=None,
                    brand_voice=None,
                    query_intent="",
                    required_agents=[],
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
                    # Add sidebar values to state for future use
                    linkedin_ids=linkedin_ids,
                    auth_codes=auth_codes,
                    urls=urls,
                    llm_provider=llm_provider
                )
                
                # Generate unique thread ID
                thread_id = str(uuid.uuid4())
                
                # Invoke the orchestrator
                result = orchestrator.app.invoke(initial_state, config={"thread_id": thread_id})
            
            # Display results
            st.success("Content generation completed!")
            
            # Create tabs for better organization
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "Blog Content", "Research Summary", "Workflow Steps", 
                "Key Insights", "Images", "Metrics"
            ])
            
            with tab1:
                st.subheader("Blog Content")
                blog_content = result.get("blog_content", "No blog content generated.")
                if blog_content != "No blog content generated.":
                    st.markdown(blog_content)
                else:
                    st.warning(blog_content)
            
            with tab2:
                st.subheader("Research Summary")
                research_summary = result.get("research_summary", "No research summary generated.")
                if research_summary != "No research summary generated.":
                    st.markdown(research_summary)
                else:
                    st.warning(research_summary)
            
            with tab3:
                st.subheader("Workflow Steps")
                processing_steps = result.get("processing_steps", [])
                if processing_steps:
                    for i, step in enumerate(processing_steps, 1):
                        st.write(f"{i}. {step}")
                else:
                    st.info("No workflow steps recorded.")
            
            with tab4:
                st.subheader("Key Insights")
                key_insights = result.get("key_insights", [])
                if key_insights:
                    for insight in key_insights:
                        st.write(f"• {insight}")
                else:
                    st.info("No key insights generated.")
            
            with tab5:
                st.subheader("Generated Images")
                generated_images = result.get("generated_images", [])
                if generated_images:
                    for img in generated_images:
                        if isinstance(img, str):
                            st.write(f"Image prompt: {img}")
                        else:
                            st.image(img)
                else:
                    st.info("No images generated.")
            
            with tab6:
                st.subheader("Content Metrics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("SEO Score", result.get("seo_score", "N/A"))
                
                with col2:
                    st.metric("Readability Score", result.get("readability_score", "N/A"))
                
                # Additional metrics if available
                quality_scores = result.get("content_quality_scores", {})
                if quality_scores:
                    st.subheader("Content Quality Scores")
                    for metric, score in quality_scores.items():
                        st.metric(metric.title(), score)
            
            # Show errors and warnings if any
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            
            if errors:
                st.error("Errors encountered:")
                for error in errors:
                    st.error(f"• {error}")
            
            if warnings:
                st.warning("Warnings:")
                for warning in warnings:
                    st.warning(f"• {warning}")
                    
        except Exception as e:
            st.error(f"An error occurred while generating content: {str(e)}")
            st.info("Please check your API key and try again.")

# Add some helpful information in the sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**How to use:**")
st.sidebar.markdown("1. Enter your OpenAI API key")
st.sidebar.markdown("2. Optionally add LinkedIn IDs, auth codes, or URLs")
st.sidebar.markdown("3. Write your content request")
st.sidebar.markdown("4. Click 'Generate Content'")

st.sidebar.markdown("---")
st.sidebar.markdown("**Example queries:**")
st.sidebar.markdown("- Write a blog post about AI in marketing")
st.sidebar.markdown("- Create content about sustainable technology")
st.sidebar.markdown("- Generate a post about remote work trends")