import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
from src.orchestrator.workflow_orchestrator import ContentMarketingOrchestrator
from src.orchestrator.state import ContentMarketingState
import uuid
import requests
import logging

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
openai_api_key = st.sidebar.text_input(api_key_label, value=os.getenv("OPENAI_API_KEY", ""), type="password")

# LinkedIn settings in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**LinkedIn Settings**")
linkedin_client_id_input = st.sidebar.text_input("LinkedIn Client ID", value=os.getenv("LINKEDIN_CLIENT_ID", ""))
linkedin_client_secret_input = st.sidebar.text_input("LinkedIn Client Secret", value=os.getenv("LINKEDIN_CLIENT_SECRET", ""), type="password")
linkedin_redirect_uri_input = st.sidebar.text_input("LinkedIn Redirect URI", value=os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8501"))

# LinkedIn OAuth helper function
def get_linkedin_auth_url(client_id: str, redirect_uri: str):
    if not client_id:
        return None
    scope = "r_liteprofile r_emailaddress w_member_social"
    return (
        f"https://www.linkedin.com/oauth/v2/authorization?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope.replace(' ', '%20')}"
    )

# Main content input
user_query = st.text_area("Enter your content request:", "Write a blog post about AI in marketing.")

if st.button("Generate Content"):
    if not openai_api_key:
        st.error("Please enter your API key in the sidebar.")
    else:
        try:
            # Set environment variable
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
            # Get LinkedIn variables for state
            linkedin_ids = st.session_state.get('linkedin_person_id', '')
            auth_codes = st.session_state.get('linkedin_auth_code', '')
            urls = st.session_state.get('urls', '')
            
            # Initialize the orchestrator
            initial_state = ContentMarketingState(
                user_query=user_query,
                linkedin_person_id=linkedin_ids,
                linkedin_auth_code=auth_codes,
                urls=urls
            )
            
            orchestrator = ContentMarketingOrchestrator()
            
            # Generate unique thread ID
            thread_id = str(uuid.uuid4())
            
            # Invoke the orchestrator
            result = orchestrator.app.invoke(initial_state, config={"thread_id": thread_id})
            
            # Store result in session state for LinkedIn publishing
            st.session_state['content_result'] = result
            
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
                st.markdown(blog_content if blog_content != "No blog content generated." else blog_content)
            
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

# LinkedIn Publishing Section (separate from content generation)
if 'content_result' in st.session_state:
    st.markdown("---")
    st.subheader("📱 LinkedIn Publishing")
    
    result = st.session_state['content_result']
    linkedin_content = result.get("linkedin_content", "")
    
    if linkedin_content and linkedin_content != "No LinkedIn content generated.":
        # Show preview of LinkedIn content
        st.markdown("**Preview of LinkedIn Content:**")
        with st.expander("Show LinkedIn Content", expanded=False):
            st.markdown(linkedin_content)
        
        # Publishing section
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🚀 Publish to LinkedIn", type="primary"):
                # Get current values
                linkedin_access_token = st.session_state.get('linkedin_access_token', '')
                linkedin_ids = st.session_state.get('linkedin_person_id', '')
                
                # Validate inputs
                if not linkedin_access_token:
                    st.error("❌ Please get your LinkedIn Access Token using the OAuth flow in the sidebar first!")
                elif not linkedin_ids:
                    st.error("❌ Please enter your LinkedIn Person ID in the sidebar first!")
                else:
                    try:
                        with st.spinner("Publishing to LinkedIn..."):
                            # Import LinkedIn agent
                            from src.agents.linkedin_connector_agent import LinkedInConnectorAgent
                        
                            # Prepare data
                            author_urn = f"urn:li:person:{linkedin_ids.strip()}"
                        
                            # Initialize and configure agent
                            agent = LinkedInConnectorAgent()
                            agent.access_token = linkedin_access_token
                        
                            # Set up logging
                            logger = logging.getLogger("streamlit_linkedin_publish")
                            if not logger.hasHandlers():
                                handler = logging.StreamHandler(sys.stdout)
                                formatter = logging.Formatter("[LOG] %(asctime)s,%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
                                handler.setFormatter(formatter)
                                logger.addHandler(handler)
                            logger.setLevel(logging.INFO)
                            logger.info("Publishing as: %s", author_urn)
                        
                            # Attempt to publish
                            response = agent.post_blog(linkedin_content, author_urn)
                        
                            if response.get("success"):
                                st.success("✅ LinkedIn post published successfully!")
                                st.balloons()
                            else:
                                error_msg = response.get('error', 'Unknown error occurred')
                                st.error(f"❌ Failed to publish: {error_msg}")
                                st.info("💡 Make sure your access token has proper permissions and is not expired.")
                            
                    except ImportError:
                        st.error("❌ LinkedInConnectorAgent not found. Please check your imports.")
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        st.info("💡 Check your network connection and API credentials.")
        
        with col2:
            if st.button("🔄 Get New Access Token"):
                st.info("Follow the OAuth flow in the sidebar to get a new access token.")
    else:
        st.warning("⚠️ No LinkedIn content available. Please generate content first.")

# LinkedIn OAuth Setup Section
st.sidebar.markdown("---")
st.sidebar.markdown("**LinkedIn OAuth Setup**")
LINKEDIN_CLIENT_ID = linkedin_client_id_input
LINKEDIN_REDIRECT_URI = linkedin_redirect_uri_input
LINKEDIN_SCOPE = "r_liteprofile w_member_social"
LINKEDIN_CLIENT_SECRET = linkedin_client_secret_input

# Step 1: LinkedIn Authentication
if st.sidebar.button("🔗 Login with LinkedIn"):
    # Set up logging to console
    logger = logging.getLogger("streamlit_linkedin_login")
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[LOG] %(asctime)s,%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Validate required fields
    if not LINKEDIN_CLIENT_ID:
        error_msg = "LinkedIn Client ID is missing. Please enter it in the sidebar."
        st.sidebar.error(error_msg)
        logger.error(error_msg)
    elif not LINKEDIN_REDIRECT_URI:
        error_msg = "LinkedIn Redirect URI is missing. Please enter it in the sidebar."
        st.sidebar.error(error_msg)
        logger.error(error_msg)
    else:
        auth_url = get_linkedin_auth_url(LINKEDIN_CLIENT_ID, LINKEDIN_REDIRECT_URI)
        try:
            st.sidebar.markdown(f"<a href='{auth_url}' target='_blank' style='font-weight:bold;'>Click here to login with LinkedIn</a>", unsafe_allow_html=True)
            st.sidebar.info("A new tab will open for LinkedIn login. After login, you will be redirected and receive an Authorization Code in the URL.")
            logger.info(f"Opening LinkedIn OAuth URL in new tab: {auth_url}")
        except Exception as e:
            error_msg = f"Failed to open LinkedIn login page: {str(e)}"
            st.sidebar.error(error_msg)
            logger.error(error_msg)

# Step 2: Handle Authorization Code
st.sidebar.markdown("---")
st.sidebar.markdown("**Step 2: Get Authorization Code**")
st.sidebar.info("After clicking the LinkedIn login link above, you'll be redirected back. Copy the 'code' parameter from the URL.")

# Show instructions more clearly
with st.sidebar.expander("📋 Instructions", expanded=True):
    st.write("1. Click the LinkedIn login link above")
    st.write("2. Enter your LinkedIn credentials")
    st.write("3. Authorize the app")
    st.write("4. You'll be redirected to a URL like:")
    st.code("http://localhost:8501?code=AQT...")
    st.write("5. Copy the 'code' value and paste below")

authorization_code = st.sidebar.text_input(
    "LinkedIn Authorization Code", 
    value="", 
    help="Paste the 'code' parameter from the URL after LinkedIn redirects you back.",
    placeholder="e.g., AQTxxx...xxx"
)

# Manual token exchange (fallback if auto-exchange fails)
if authorization_code and not st.session_state.get('linkedin_access_token'):
    if st.sidebar.button("🔑 Manual Token Exchange"):
        # Set up logging
        logger = logging.getLogger("streamlit_linkedin_manual_token")
        if not logger.hasHandlers():
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("[LOG] %(asctime)s,%(msecs)03d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        if LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET and LINKEDIN_REDIRECT_URI:
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": LINKEDIN_REDIRECT_URI,
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            try:
                logger.info("Manual token exchange...")
                response = requests.post(token_url, data=data, headers=headers)
                
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data.get("access_token")
                    
                    if access_token:
                        st.sidebar.success("✅ Access Token received manually!")
                        st.session_state['linkedin_access_token'] = access_token
                        st.session_state['linkedin_auth_code'] = authorization_code
                        st.rerun()
                    else:
                        st.sidebar.error("❌ No access token in response")
                else:
                    st.sidebar.error(f"❌ Failed to get access token: {response.text}")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Error in manual token exchange: {str(e)}")
        else:
            st.sidebar.error("❌ Missing LinkedIn credentials")

# Additional LinkedIn settings
st.sidebar.markdown("---")
st.sidebar.markdown("**LinkedIn Publishing Info**")

# Add LinkedIn person ID field
linkedin_person_id = st.sidebar.text_input(
    "LinkedIn Person ID", 
    value=st.session_state.get('linkedin_person_id', ''),
    help="Your LinkedIn person ID (numbers only, e.g., 123456789)"
)
if linkedin_person_id:
    st.session_state['linkedin_person_id'] = linkedin_person_id

# Show current OAuth status
if st.session_state.get('linkedin_access_token'):
    st.sidebar.success("✅ LinkedIn OAuth Complete")
    st.sidebar.write(f"🔑 Token: {st.session_state['linkedin_access_token'][:20]}...")
    if st.sidebar.button("🗑️ Clear Token"):
        if 'linkedin_access_token' in st.session_state:
            del st.session_state['linkedin_access_token']
        if 'linkedin_auth_code' in st.session_state:
            del st.session_state['linkedin_auth_code']
        st.rerun()
else:
    st.sidebar.info("ℹ️ Complete OAuth flow above to publish to LinkedIn")

# Add some helpful information in the sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**How to use:**")
st.sidebar.markdown("1. Enter your API key")
st.sidebar.markdown("2. Set LinkedIn OAuth credentials")
st.sidebar.markdown("3. Complete LinkedIn OAuth flow")
st.sidebar.markdown("4. Write your content request")
st.sidebar.markdown("5. Click 'Generate Content'")
st.sidebar.markdown("6. Click 'Publish to LinkedIn'")

st.sidebar.markdown("---")
st.sidebar.markdown("**Example queries:**")
st.sidebar.markdown("- Write a blog post about AI in marketing")
st.sidebar.markdown("- Create content about sustainable technology")
st.sidebar.markdown("- Generate a post about remote work trends")