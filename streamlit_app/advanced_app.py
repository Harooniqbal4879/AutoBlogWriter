import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["NGROK_PATH"] = r"C:\ngrok\ngrok.exe"  # Update this path if you installed ngrok elsewhere
from dotenv import load_dotenv
import streamlit as st
from pyngrok import ngrok

from src.orchestrator.workflow_orchestrator import ContentMarketingOrchestrator
# If you have a different orchestrator file, update the import above

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

def print_env():
    print('OPENAI_API_KEY:', OPENAI_API_KEY)
    print('LANGCHAIN_API_KEY:', LANGCHAIN_API_KEY)

if __name__ == "__main__":
    print_env()

st.set_page_config(
    page_title="AI Content Marketing Assistant",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 AI Content Marketing Assistant")
st.markdown("*Multi-Agent Content Creation System*")

ngrok_tunnel = None
if st.sidebar.button("Start ngrok Tunnel for OAuth2 Redirect"):
    ngrok_tunnel = ngrok.connect(8501, bind_tls=True)
    st.sidebar.success(f"ngrok tunnel started: {ngrok_tunnel.public_url}")
    st.sidebar.write(f"Use this URL as your LinkedIn Redirect URI.")

with st.sidebar:
    st.header("Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Required for content generation")
    serp_key = st.text_input("SERP API Key (Optional)", type="password", help="For enhanced web research")
    model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"], help="Choose the AI model")
    with st.expander("Advanced Settings"):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        max_tokens = st.slider("Max Tokens", 500, 3000, 2000)

    st.header("LinkedIn Auto-Posting")
    linkedin_client_id = st.text_input("LinkedIn Client ID")
    linkedin_client_secret = st.text_input("LinkedIn Client Secret", type="password")
    linkedin_redirect_uri = st.text_input("LinkedIn Redirect URI")
    linkedin_auth_code = st.text_input("LinkedIn Authorization Code (after user authorization)")
    linkedin_urn = st.text_input("Your LinkedIn URN (e.g., 123456789)")
    linkedin_access_token = st.text_input("LinkedIn Access Token (fetched after authorization)", type="password")

    # LinkedIn Posting Agent UI
    try:
        from src.agents.linkedin_posting_agent import LinkedInPostingAgent
        if st.button("Get LinkedIn Authorization URL"):
            agent = LinkedInPostingAgent(linkedin_client_id, linkedin_client_secret, linkedin_redirect_uri)
            st.write("Authorize your app here:", agent.get_authorization_url())
        if st.button("Fetch LinkedIn Access Token"):
            agent = LinkedInPostingAgent(linkedin_client_id, linkedin_client_secret, linkedin_redirect_uri)
            try:
                agent.fetch_access_token(linkedin_auth_code)
                st.session_state['linkedin_access_token'] = agent.access_token
                st.success("Access token fetched and stored in session.")
            except Exception as e:
                st.error(f"Failed to fetch access token: {e}")
        if st.button("Post to LinkedIn"):
            agent = LinkedInPostingAgent(linkedin_client_id, linkedin_client_secret, linkedin_redirect_uri)
            agent.access_token = linkedin_access_token or st.session_state.get('linkedin_access_token')
            post_text = ""
            if 'conversation_history' in st.session_state and st.session_state.conversation_history:
                for msg in reversed(st.session_state.conversation_history):
                    if isinstance(msg, dict) and 'content' in msg and 'LinkedIn Post' in msg['content']:
                        post_text = msg['content']
                        break
            if not post_text:
                post_text = st.text_area("LinkedIn Post Content", value="", help="Paste your LinkedIn post here.")
            try:
                result = agent.post_linkedin(post_text, linkedin_urn)
                st.success("Posted to LinkedIn!")
                st.write("Post result:", result)
            except Exception as e:
                st.error(f"Failed to post to LinkedIn: {e}")
    except ImportError:
        st.info("LinkedInPostingAgent not found. Please add src/agents/linkedin_posting_agent.py.")

if not openai_key:
    st.warning("Please enter your OpenAI API key in the sidebar to continue.")
    st.stop()

class Config:
    def __init__(self, openai_api_key, serp_api_key, model, temperature, max_tokens):
        self.openai_api_key = openai_api_key
        self.serp_api_key = serp_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

config = Config(
    openai_api_key=openai_key,
    serp_api_key=serp_key,
    model=model,
    temperature=temperature,
    max_tokens=max_tokens
)

if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = ContentMarketingOrchestrator(config.__dict__)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

st.header("💬 Content Creation Chat")
for i, message in enumerate(st.session_state.conversation_history):
    if message['role'] == 'user':
        with st.chat_message("user"):
            st.write(message['content'])
    else:
        with st.chat_message("assistant"):
            st.write(message['content'])

user_input = st.chat_input("Describe the content you want to create...")

if user_input:
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': user_input
    })
    with st.chat_message("user"):
        st.write(user_input)
    with st.chat_message("assistant"):
        with st.spinner("Creating content with AI agents..."):
            result = st.session_state.orchestrator.process_request(
                user_input,
                st.session_state.conversation_history
            )
        if result['metadata']['success']:
            st.success("Content created successfully!")
            tabs = st.tabs(["📊 Overview", "📝 Blog", "💼 LinkedIn", "🎨 Images", "📈 Strategy"])
            with tabs[0]:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Quality Score", f"{result['metadata'].get('quality_score', 0)}/100")
                with col2:
                    st.metric("Content Type", result['content_type'].title())
                with col3:
                    st.metric("Generated Items", len([k for k in result['generated_content'] if result['generated_content'][k]]))
            with tabs[1]:
                blog_result = result['generated_content'].get('blog')
                if blog_result:
                    st.markdown("### SEO-Optimized Blog Post")
                    if hasattr(blog_result, 'content'):
                        st.markdown(blog_result.content)
                    else:
                        st.markdown(str(blog_result))
                    if result['generated_content'].get('blog_metadata'):
                        meta = result['generated_content']['blog_metadata']
                        st.info(f"📊 {meta.get('word_count', 0)} words • {meta.get('estimated_read_time', 0)} min read")
                else:
                    st.info("No blog content generated for this request.")
            with tabs[2]:
                if result['generated_content'].get('linkedin'):
                    st.markdown("### LinkedIn Post")
                    st.markdown(result['generated_content']['linkedin'])
                    if result['generated_content'].get('linkedin_metadata'):
                        meta = result['generated_content']['linkedin_metadata']
                        st.info(f"📊 Engagement Score: {meta.get('engagement_score', 0)}/100 • {len(meta.get('hashtags', []))} hashtags")
                else:
                    st.info("No LinkedIn content generated for this request.")
            with tabs[3]:
                if result['images']:
                    st.markdown("### Generated Images")
                    for i, image in enumerate(result['images']):
                        if image.startswith('http'):
                            st.image(image, caption=f"Generated Image {i+1}")
                        else:
                            st.markdown(f"**Image Concept {i+1}:**")
                            st.markdown(image)
                else:
                    st.info("No images generated for this request.")
            with tabs[4]:
                if result['generated_content'].get('strategy'):
                    st.markdown("### Content Strategy Recommendations")
                    st.markdown(result['generated_content']['strategy'])
                else:
                    st.info("No strategy content generated for this request.")
            if result['research_data'].get('content'):
                with st.expander("🔍 Research Data"):
                    st.markdown(result['research_data']['content'])
        else:
            st.error("Content creation failed!")
            st.error(f"Errors: {', '.join(result['error_log'])}")
    st.session_state.conversation_history.append({
        'role': 'assistant',
        'content': f"Generated {result['content_type']} content with quality score: {result['metadata'].get('quality_score', 0)}/100"
    })

if st.button("🗑️ Clear Conversation"):
    st.session_state.conversation_history = []
    st.rerun()
