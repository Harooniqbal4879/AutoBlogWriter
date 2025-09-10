# AutoBlogWriter Release 1.0

Date: 2025-09-10

Highlights:
- Streamlit UI improvements: cleaner sidebar, editable LinkedIn credentials, and env-backed defaults for OpenAI/LinkedIn keys.
- LinkedIn OAuth: "Login with LinkedIn" now opens in a new tab with proper client ID and redirect parameters.
- Publishing: LinkedIn post button publishes LinkedInWriterAgent content only; added logging for button actions and errors.
- Config: Centralized .env loading and typed config in `src/utils/config.py`.
- Added scaffold `src/linkedin_oauth_app.py` for future enhancements.

Notes:
- Ensure the LinkedIn redirect URI matches the Streamlit port (default 8501) exactly in the LinkedIn developer portal.
- Generated images are not tracked in Git to keep the repo lean.

