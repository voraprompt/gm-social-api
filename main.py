from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

RAPIDAPI_KEY = "fe64982d69msh9912a3389f014cfp15b50bjsn7c1175c1ff2d"
RAPIDAPI_HOST = "auto-download-all-in-one-big.p.rapidapi.com"

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader Backend Active!"}

@app.post("/extract")
def extract_video(req: VideoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is empty")

    # 1. TIKTOK ENGINE
    if "tiktok.com" in url:
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=10).json()
            if r.get("code") == 0 and "play" in r.get("data", {}):
                link = r["data"]["play"]
                if not link.startswith("http"):
                    link = "https://www.tikwm.com" + link
                return {"status": "success", "download_url": link}
        except Exception:
            pass

    # 2. YOUTUBE ENGINE (Direct yt-dlp Python API)
    if "youtube.com" in url or "youtu.be" in url:
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if direct_url:
                    return {"status": "success", "download_url": direct_url}
        except Exception as e:
            print("YTDLP Error:", e)

    # 3. RAPIDAPI ENGINE (Instagram, Facebook, Twitter etc.)
    try:
        rapid_url = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        resp = requests.post(rapid_url, json={"url": url}, headers=headers, timeout=12)
        res_json = resp.json()

        # Recursive search in JSON
        def find_url(data):
            if isinstance(data, str) and data.startswith("http"):
                if any(ext in data.lower() for ext in [".mp4", "googlevideo", "cdn"]):
                    return data
            elif isinstance(data, dict):
                for k, v in data.items():
                    res = find_url(v)
                    if res: return res
            elif isinstance(data, list):
                for item in data:
                    res = find_url(item)
                    if res: return res
            return None

        found = find_url(res_json)
        if found:
            return {"status": "success", "download_url": found}
    except Exception:
        pass

    raise HTTPException(status_code=400, detail="Extraction failed for this URL")
