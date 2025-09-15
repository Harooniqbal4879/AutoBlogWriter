import os
import json

BLOG_FILE = "blog_content.json"

def save_blog_content(content):
    with open(BLOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"blog_content": content}, f)

def load_blog_content():
    if os.path.exists(BLOG_FILE):
        with open(BLOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("blog_content", "")
    return ""

def clear_blog_content():
    if os.path.exists(BLOG_FILE):
        os.remove(BLOG_FILE)
