from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# CORS configuration to allow your app to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader API is Running!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)

            direct_url = info.get('url')
            title = info.get('title', 'GM_Video')
            thumbnail = info.get('thumbnail', '')

            return {
                "status": "success",
                "title": title,
                "download_url": direct_url,
                "thumbnail": thumbnail
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
