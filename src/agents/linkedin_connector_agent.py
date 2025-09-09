import os
import openai
import requests
from typing import Dict, Any
from src.utils.config import Config

class LinkedInConnectorAgent:
    """
    Agent to post generated blog content to LinkedIn using LinkedIn API.
    """
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.api_url = "https://api.linkedin.com/v2/ugcPosts"

    def post_blog(self, blog_content: str, author_urn: str) -> Dict[str, Any]:
        if not self.access_token:
            return {"success": False, "error": "LinkedIn access token not set."}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": blog_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 201:
                return {"success": True, "message": "Blog posted to LinkedIn successfully."}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
