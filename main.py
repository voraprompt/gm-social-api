import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

class LinkRequest(BaseModel):
    url: str

@app.post("/extract")
async def extract_video(request: LinkRequest):
    video_url = request.url
    
    # Check if cookies file exists
    cookie_path = "cookies.txt"
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    # Agar cookies file maujood hai toh usse use karein
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url', None)
            
            if not download_url:
                raise HTTPException(status_code=400, detail="Could not extract download URL")
                
            return {"download_url": download_url, "title": info.get('title')}
            
    except Exception as e:
        error_msg = str(e)
        # User friendly error message
        if "confirm you're not a bot" in error_msg:
            return {"error": "YouTube blocked the request. Update cookies.txt on server."}
        raise HTTPException(status_code=500, detail=error_msg)
