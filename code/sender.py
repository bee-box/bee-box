import requests
import json
from datetime import datetime
import time
import argparse
import pytz
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_scheduled_ghost_post(api_url=None, admin_key=None, title=None, html_content=None, 
                               scheduled_time=None, tags=None, featured=False):
    """
    Create a scheduled post on a Ghost.io blog
    """
    # Use environment variables if parameters not provided
    api_url = api_url or os.getenv('GHOST_API_URL')
    admin_key = admin_key or os.getenv('GHOST_ADMIN_API_KEY')
    
    if not api_url or not admin_key:
        raise ValueError("Ghost API URL and Admin API Key must be provided either as parameters or environment variables")
    
    # Ensure the scheduled_time is in the correct format
    if isinstance(scheduled_time, datetime):
        # Convert to ISO 8601 format with timezone info
        scheduled_time = scheduled_time.isoformat()
    
    # Prepare the request headers
    headers = {
        'Authorization': f'Ghost {admin_key}',
        'Content-Type': 'application/json'
    }
    
    # Prepare the post data
    post_data = {
        "posts": [{
            "title": title,
            "html": html_content,
            "status": "scheduled",
            "published_at": scheduled_time,
            "featured": featured
        }]
    }
    
    # Add tags if provided
    if tags:
        post_data["posts"][0]["tags"] = [{"name": tag} for tag in tags]
    
    # Make the API request
    endpoint = f"{api_url.rstrip('/')}/posts/"
    response = requests.post(endpoint, headers=headers, json=post_data)
    
    # Check for success
    if response.status_code >= 200 and response.status_code < 300:
        return response.json()
    else:
        raise Exception(f"Failed to create post. Status code: {response.status_code}, "
                        f"Response: {response.text}")

# ... rest of the script remains the same ...

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Schedule a Ghost blog post')
    parser.add_argument('--url', help='Ghost Admin API URL (defaults to GHOST_API_URL env var)')
    parser.add_argument('--key', help='Ghost Admin API Key (defaults to GHOST_ADMIN_API_KEY env var)')
    parser.add_argument('--title', required=True, help='Post title')
    parser.add_argument('--content', required=True, help='HTML content or path to HTML file')
    parser.add_argument('--time', required=True, 
                        help='Scheduled time in ISO format (e.g., 2025-05-20T15:00:00Z)')
    parser.add_argument('--tags', help='Comma-separated list of tags')
    parser.add_argument('--featured', action='store_true', help='Set post as featured')
    parser.add_argument('--wait', action='store_true', 
                        help='Wait until scheduled time to ensure publication')
    
    args = parser.parse_args()
    
    # ... rest of the code remains the same ...