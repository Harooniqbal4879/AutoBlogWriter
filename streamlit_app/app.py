import sys
import os
import uuid
import logging
import requests
import urllib.parse
from typing import Optional, Dict, Any
import streamlit as st
from streamlit_app.blog_persistence import save_blog_content, load_blog_content, clear_blog_content

# Make src importable (adjust if your project layout differs)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.orchestrator.workflow_orchestrator import ContentMarketingOrchestrator
from src.orchestrator.state import ContentMarketingState

# Must be the first Streamlit command
st.set_page_config(
    page_title="AutoBlogWriter",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded",
)


# Logging
logger = logging.getLogger("linkedin_oauth")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[LOG] %(asctime)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
# Also log to file for debugging
file_handler = logging.FileHandler("debug.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Test log message
# logger.info("Test log message: logger setup complete")

st.title("AutoBlogWriter: Intelligent Content Creation")

# ----------------------------
# Helpers
# ----------------------------
def get_linkedin_auth_url(client_id: str, redirect_uri: str, scope: str) -> Optional[str]:
    if not client_id:
        return None
    state = str(uuid.uuid4())
    return (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&state={state}"
    )

def post_to_linkedin_api(access_token: str, message: str) -> Dict[str, Any]:
    if not access_token:
        return {"success": False, "error": "No access token provided"}
    url = "https://api.linkedin.com/v2/ugcPosts"
    post_data = {
        #"author": "urn:li:person:<member_id>",
        #"author": "urn:li:member:<numeric_id>",
        "author": "urn:li:organization:<organization_id>",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    try:
        resp = requests.post(url, json=post_data, headers=headers, timeout=20)
        if resp.status_code in (200, 201):
            return {"success": True, "response": resp.json()}
        try:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.json()}"}
        except Exception:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_linkedin_token(access_token: str, requested_scope: str) -> bool:
    if not access_token:
        return False
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def extract_code_from_url(url: str) -> str:
    """Extract authorization code from LinkedIn callback URL"""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        code = urllib.parse.parse_qs(parsed.query).get("code", [""])[0]
        return code
    except Exception:
        return ""

def get_access_token(client_id: str, client_secret: str, redirect_uri: str, auth_code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token"""
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    
    try:
        resp = requests.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            try:
                error_data = resp.json()
                return {"success": False, "error": error_data.get("error_description", "Unknown error")}
            except:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------------------
# Sidebar: LinkedIn OAuth Flow
# ----------------------------
st.sidebar.title("LinkedIn OAuth Setup")

# Step 1: LinkedIn App Credentials
st.sidebar.markdown("### 🔐 Step 1: LinkedIn App Credentials")
LINKEDIN_CLIENT_ID = "868ac47cwrbkde"
LINKEDIN_CLIENT_SECRET = "WPL_AP1.HSQMVkswWCBfufAr.6sCCSw=="
LINKEDIN_REDIRECT_URI = st.sidebar.text_input(
    "LinkedIn Redirect URI",
    value=os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8501/linkedin/callback"),
    key="linkedin_redirect_uri",
)
LINKEDIN_SCOPE = "w_member_social r_basicprofile openid profile email w_organization_social"

# Step 2: Authentication
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Step 2: LinkedIn Authentication")

# Check if we already have valid credentials
credentials_valid = bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET and LINKEDIN_REDIRECT_URI)

if not credentials_valid:
    st.sidebar.warning("⚠️ Please fill in LinkedIn credentials above")
else:
    # Generate and display auth URL
    auth_url = get_linkedin_auth_url(LINKEDIN_CLIENT_ID, LINKEDIN_REDIRECT_URI, LINKEDIN_SCOPE)
    
    if auth_url:
        st.sidebar.markdown(
            f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                <p><strong>Click the link below to authenticate:</strong></p>
                <a href="{auth_url}" target="_blank" style="color: #0073b1; text-decoration: none; font-weight: bold;">
                    🔗 Login with LinkedIn
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

# Step 3: Authorization Code Extraction
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Step 3: Authorization Code")

# Auto-detect code from URL parameters
try:
    code_from_url = st.query_params.get("code")  # Streamlit >= 1.36
except Exception:
    try:
        code_from_url = st.experimental_get_query_params().get("code", [None])[0]
    except:
        code_from_url = None

# Display current auth code (auto-detected or manual)
if code_from_url:
    st.sidebar.success("✅ Authorization code detected automatically!")
    st.sidebar.code(code_from_url, language="text")
    st.session_state["linkedin_auth_code"] = code_from_url
else:
    st.sidebar.info("ℹ️ No authorization code detected in URL")

# Manual input option
manual_url = st.sidebar.text_area(
    "Or paste the full callback URL here:",
    placeholder="http://localhost:8501/linkedin/callback?code=AQT...",
    help="Paste the entire URL you were redirected to after LinkedIn authentication",
    key="manual_callback_url"
)

if manual_url:
    extracted_code = extract_code_from_url(manual_url)
    if extracted_code:
        st.sidebar.success("✅ Code extracted successfully!")
        st.sidebar.code(extracted_code, language="text")
        st.session_state["linkedin_auth_code"] = extracted_code
    else:
        st.sidebar.error("❌ No valid code found in URL")

# Display current auth code status
current_code = st.session_state.get("linkedin_auth_code", "")
if current_code:
    st.sidebar.markdown(f"**Current Auth Code:** `{current_code[:20]}...`")

# Step 4: Get Access Token
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Step 4: Get Access Token")

access_token = st.session_state.get("linkedin_access_token")
if access_token:
    if validate_linkedin_token(access_token, LINKEDIN_SCOPE):
        st.sidebar.success("✅ Valid Access Token Available")
        st.sidebar.markdown(f"**Token:** `{access_token[:15]}...`")
        
        # Clear token button
        if st.sidebar.button("🗑️ Clear Token", key="clear_token"):
            for k in ["linkedin_access_token", "linkedin_auth_code"]:
                st.session_state.pop(k, None)
            st.rerun()
    else:
        st.sidebar.error("❌ Token Invalid/Expired")
        st.session_state.pop("linkedin_access_token", None)
else:
    if current_code and credentials_valid:
        if st.sidebar.button("🔑 Get Access Token", type="primary", key="get_access_token"):
            with st.sidebar:
                with st.spinner("Exchanging code for access token..."):
                    result = get_access_token(
                        LINKEDIN_CLIENT_ID,
                        LINKEDIN_CLIENT_SECRET, 
                        LINKEDIN_REDIRECT_URI,
                        current_code
                    )
                
                if result["success"]:
                    token_data = result["data"]
                    access_token = token_data.get("access_token")
                    
                    if access_token and validate_linkedin_token(access_token, LINKEDIN_SCOPE):
                        st.session_state["linkedin_access_token"] = access_token
                        st.sidebar.success("✅ Access Token obtained successfully!")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Received token but validation failed")
                else:
                    st.sidebar.error(f"❌ Token exchange failed: {result['error']}")
    else:
        if not current_code:
            st.sidebar.warning("⚠️ Authorization code required")
        if not credentials_valid:
            st.sidebar.warning("⚠️ LinkedIn credentials required")

# Step 5: Person ID and Testing
st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Step 5: LinkedIn Person ID (Optional)")

linkedin_person_id = st.sidebar.text_input(
    "LinkedIn Person ID",
    value=st.session_state.get("linkedin_person_id", ""),
    help="Only required for certain LinkedIn APIs. Numbers only.",
    key="linkedin_person_id",
)

# Step 6: Test Post
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Step 6: Test LinkedIn Post")

if st.session_state.get("linkedin_access_token"):
    custom_message = st.sidebar.text_area(
        "Test message:",
        "Hello World! 🌍 Posted via my AutoBlogWriter app! #HelloWorld #LinkedInAPI",
        height=80,
        key="sidebar_test_message"
    )
    
    if st.sidebar.button("📤 Post to LinkedIn", type="primary", key="sidebar_post_test"):
        access_token = st.session_state.get("linkedin_access_token")
        
        with st.sidebar:
            with st.spinner("Posting to LinkedIn..."):
                result = post_to_linkedin_api(access_token, custom_message.strip())
                
            if result.get("success"):
                st.sidebar.success("✅ Posted successfully!")
                st.balloons()
            else:
                st.sidebar.error(f"❌ Post failed: {result.get('error', 'Unknown error')}")
else:
    st.sidebar.info("ℹ️ Complete OAuth flow above to test posting")

# ----------------------------
# Main Content Area: LLM Settings & Content Generation
# ----------------------------

# LLM Settings (moved to main area)
st.markdown("## ⚙️ LLM Configuration")

col1, col2 = st.columns(2)

with col1:
    llm_provider = st.selectbox(
        "LLM Provider",
        ["OpenAI", "Claude", "Gemini", "Perplexity", "Tavily"],
        index=0,
        key="llm_provider",
    )

with col2:
    api_key_labels = {
        "OpenAI": "OpenAI API Key",
        "Claude": "Anthropic API Key", 
        "Gemini": "Google Gemini API Key",
        "Perplexity": "Perplexity API Key",
        "Tavily": "Tavily API Key",
    }
    api_key_label = api_key_labels.get(llm_provider, "API Key")
    api_key_value = st.text_input(
        api_key_label,
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        key="llm_api_key",
    )

# Content Generation

st.markdown("---")
st.markdown("## 📝 Content Generation")

# Load persisted blog content if available
persisted_blog_content = load_blog_content()

user_query = st.text_area(
    "Enter your content request:",
    "Write a blog post about AI in marketing.",
    key="content_request",
    height=100
)

# Show persisted blog content on refresh
if persisted_blog_content:
    st.info("Last generated blog post (persisted):")
    import re
    st.markdown(re.sub(r"#[\w]+", "", persisted_blog_content))
    if st.button("🧹 Clear & Start New Blog", key="btn_clear_blog_top"):
        clear_blog_content()
        st.success("Blog content cleared. You can start a new blog.")

if st.button("Generate Content", key="btn_generate_content", type="primary"):
    if not api_key_value:
        st.error("Please enter your API key above.")
    else:
        try:
            os.environ["OPENAI_API_KEY"] = api_key_value

            initial_state = ContentMarketingState(
                user_query=user_query,
                linkedin_person_id=st.session_state.get("linkedin_person_id", ""),
                linkedin_auth_code=st.session_state.get("linkedin_auth_code", ""),
                urls=st.session_state.get("urls", ""),
            )

            with st.spinner("Generating content..."):
                orchestrator = ContentMarketingOrchestrator()
                result = orchestrator.app.invoke(initial_state, config={"thread_id": str(uuid.uuid4())})
                st.session_state["content_result"] = result
            
            st.success("Content generation completed!")

            tab6, tab1, tab2, tab3, tab4, tab5, tab7 = st.tabs(
                [
                    "📊 Metrics",
                    "📝 Blog Content",
                    "🔬 Research Summary",
                    "🛠️ Workflow Steps",
                    "💡 Key Insights",
                    "🖼️ Images",
                    "💼 LinkedIn Content"
                ]
            )

            # Persist blog content
            blog_content = result.get("blog_content", "No blog content generated.")
            save_blog_content(blog_content)

            with tab1:
                st.subheader("Blog Content")
                # Remove hashtags from blog content
                import re
                blog_content_no_hashtags = re.sub(r"#[\w]+", "", blog_content)
                st.markdown(blog_content_no_hashtags)
                if st.button("🧹 Clear & Start New Blog", key="btn_clear_blog"):
                    clear_blog_content()
                    st.success("Blog content cleared. You can start a new blog.")

            with tab2:
                st.subheader("Research Summary")
                summary = result.get("research_summary", "No research summary generated.")
                if summary and summary != "No research summary generated.":
                    st.markdown(summary)
                else:
                    st.info(summary)

            with tab3:
                st.subheader("Workflow Steps")
                steps = result.get("processing_steps", [])
                if steps:
                    for i, step in enumerate(steps, 1):
                        st.write(f"{i}. {step}")
                else:
                    st.info("No workflow steps recorded.")

            with tab4:
                st.subheader("Key Insights")
                insights = result.get("key_insights", [])
                if insights:
                    for insight in insights:
                        st.write(f"• {insight}")
                else:
                    st.info("No key insights generated.")

            with tab5:
                st.subheader("Generated Images")
                images = result.get("generated_images", [])
                if images:
                    for img in images:
                        if isinstance(img, str):
                            st.write(f"Image prompt: {img}")
                        else:
                            st.image(img)
                else:
                    st.info("No images generated.")

            with tab6:
                st.subheader("Content Metrics")
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("SEO Score", result.get("seo_score", "N/A"))
                with c2:
                    st.metric("Readability Score", result.get("readability_score", "N/A"))
                quality = result.get("content_quality_scores", {})
                if quality:
                    st.subheader("Content Quality Scores")
                    for metric, score in quality.items():
                        st.metric(metric.title(), score)

            with tab7:
                st.subheader("LinkedIn Content")
                linkedin_content = result.get("linkedin_content", "No LinkedIn content generated.")
                st.markdown(linkedin_content)
                st.markdown("---")
                st.markdown("## 📱 Publish LinkedIn Content")
                access_token = st.session_state.get("linkedin_access_token", "")
                LINKEDIN_SCOPE = "w_member_social r_basicprofile openid profile email w_organization_social"
                if linkedin_content and linkedin_content != "No LinkedIn content generated.":
                    st.markdown("**Preview of Generated LinkedIn Content:**")
                    with st.expander("Show LinkedIn Content", expanded=True):
                        st.markdown(linkedin_content)
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("🚀 Publish Generated Content", type="primary", key="btn_publish_generated_tab7"):
                            if not access_token:
                                st.error("❌ Missing Access Token. Complete the OAuth flow in the sidebar first!")
                            elif not validate_linkedin_token(access_token, LINKEDIN_SCOPE):
                                st.error("❌ Access Token is invalid or expired. Please get a new one.")
                            else:
                                with st.spinner("Publishing to LinkedIn..."):
                                    res = post_to_linkedin_api(access_token, linkedin_content)
                                    if res.get("success"):
                                        st.success("✅ Generated content posted to LinkedIn successfully!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Failed to post: {res.get('error', 'Unknown error occurred')}")
                    with col2:
                        custom_linkedin_content = st.text_area(
                            "Edit content before posting:",
                            value=linkedin_content,
                            height=150,
                            key="custom_linkedin_content_tab7"
                        )
                        if st.button("📝 Publish Edited Content", key="btn_publish_edited_tab7"):
                            if not access_token:
                                st.error("❌ Missing Access Token. Complete the OAuth flow in the sidebar first!")
                            elif not validate_linkedin_token(access_token, LINKEDIN_SCOPE):
                                st.error("❌ Access Token is invalid or expired. Please get a new one.")
                            else:
                                with st.spinner("Publishing to LinkedIn..."):
                                    res = post_to_linkedin_api(access_token, custom_linkedin_content)
                                    if res.get("success"):
                                        st.success("✅ Edited content posted to LinkedIn successfully!")
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Failed to post: {res.get('error', 'Unknown error occurred')}")
                else:
                    st.info("No LinkedIn content was generated. Try generating content first.")


            if result.get("errors"):
                st.error("Errors encountered:")
                for err in result["errors"]:
                    st.error(f"• {err}")
            if result.get("warnings"):
                st.warning("Warnings:")
                for warn in result["warnings"]:
                    st.warning(f"• {warn}")

        except Exception as e:
            st.error(f"An error occurred while generating content: {str(e)}")
            st.info("Please check your API key and try again.")

## LinkedIn publishing UI removed from all tabs except 'LinkedIn Content' tab