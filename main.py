from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import re
import os  # Import os for environment variables

app = FastAPI()

class PostURL(BaseModel):
    url: str

def detect_platform(url: str):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "tiktok.com" in url:
        return "TikTok"
    else:
        return None

def extract_youtube_video_id(url):
    pattern = r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.post("/extract-comments")
def extract_comments(data: PostURL):
    url = data.url
    platform = detect_platform(url)

    if not platform:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    if platform == "YouTube":
        video_id = extract_youtube_video_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        api_key = os.getenv("YOUTUBE_API_KEY")  # Get YouTube API key from environment

        if not api_key:
            raise HTTPException(status_code=500, detail="Missing YouTube API Key")

        youtube_api_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}"

        response = requests.get(youtube_api_url)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error fetching YouTube comments")

        comments = [
            {"username": item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
             "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
             "timestamp": item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]}
            for item in response.json().get("items", [])
        ]
        return {"platform": "YouTube", "comments": comments}

    elif platform == "Instagram" or platform == "TikTok":
        raise HTTPException(status_code=501, detail="Instagram & TikTok API requires authentication")

    return {"platform": platform, "comments": []}
