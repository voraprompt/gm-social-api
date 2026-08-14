from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import re

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

def unshorten_url(url: str) -> str:
    """Expand shortened links like vt.tiktok.com or youtu.be to full destination URLs"""
    try:
        session = requests.Session()
        resp = session.head(url, allow_redirects=True, timeout=5)
        return resp.url
    except Exception:
        return url

def extract_direct_media_url(data):
    """Deep search for playable media link in API response"""
    if isinstance(data, str) and data.startswith("http"):
        if any(ext in data.lower() for ext in [".mp4", "googlevideo", "tiktokcdn", "cdninstagram"]):
            return data
    elif isinstance(data, dict):
        # Priority keys used by social downloader APIs
        for key in ["url", "download_url", "play", "no_watermark", "video_url", "link"]:
            if key in data and isinstance(data[key], str) and data[key].startswith("http"):
                return data[key]
        for val in data.values():
            res = extract_direct_media_url(val)
            if res:
                return res
    elif isinstance(data, list):
        for item in data:
            res = extract_direct_media_url(item)
            if res:
                return res
    return None

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader Backend Active!"}

@app.post("/extract")
def extract_video(req: VideoRequest):
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # Expand short links first
    target_url = unshorten_url(raw_url)

    # 1. TIKTOK DEDICATED ENGINE
    if "tiktok.com" in target_url:
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": target_url}, timeout=8).json()
            if r.get("code") == 0 and "play" in r.get("data", {}):
                link = r["data"]["play"]
                if not link.startswith("http"):
                    link = "https://www.tikwm.com" + link
                return {"status": "success", "download_url": link}
        except Exception:
            pass

    # 2. UNIVERSAL RAPIDAPI ENGINE (YouTube, Instagram, Facebook, Twitter)
    try:
        rapid_endpoint = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        
        resp = requests.post(rapid_endpoint, json={"url": target_url}, headers=headers, timeout=12)
        
        if resp.status_code == 200:
            res_json = resp.json()
            media_link = extract_direct_media_url(res_json)
            if media_link:
                return {"status": "success", "download_url": media_link}
    except Exception as e:
        print("RapidAPI Exception:", e)

    raise HTTPException(status_code=400, detail="Extraction failed for this URL")
