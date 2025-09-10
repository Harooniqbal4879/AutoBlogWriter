from flask import Flask, redirect, request
import os
import requests

app = Flask(__name__)

# Load LinkedIn credentials from environment variables
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/linkedin/callback"

@app.route("/")
def home():
    return '<a href="/login">Login with LinkedIn</a>'

@app.route("/login")
def login():
    # Redirect user to LinkedIn's OAuth 2.0 authorization page
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        "?response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=r_liteprofile%20r_emailaddress%20w_member_social"
    )
    return redirect(auth_url)

@app.route("/linkedin/callback")
def linkedin_callback():
    # Get authorization code from LinkedIn
    code = request.args.get("code")
    # Exchange code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    return f"Access Token: {access_token}"

if __name__ == "__main__":
    app.run(debug=True)
