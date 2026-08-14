from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

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

def extract_url_from_json(data):
    """Deep search for any playable mp4/video link in JSON response"""
    if isinstance(data, str) and data.startswith("http"):
        if any(ext in data.lower() for ext in [".mp4", "googlevideo.com", "cdn", "tiktokcdn"]):
            return data
    elif isinstance(data, dict):
        # Priority keys
        for key in ["url", "download_url", "play", "link"]:
            if key in data and isinstance(data[key], str) and data[key].startswith("http"):
                return data[key]
        for val in data.values():
            found = extract_url_from_json(val)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = extract_url_from_json(item)
            if found:
                return found
    return None

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader Backend Active!"}

@app.post("/extract")
def extract_video(req: VideoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # 1. TIKTOK DIRECT ENGINE
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

    # 2. YOUTUBE SHORTS ENGINE
    if "youtube.com" in url or "youtu.be" in url:
        try:
            video_id = ""
            if "shorts/" in url:
                video_id = url.split("shorts/")[1].split("?")[0].split("/")[0]
            elif "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]

            if video_id:
                inv = requests.get(f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}", timeout=8).json()
                streams = inv.get("formatStreams", [])
                if streams:
                    return {"status": "success", "download_url": streams[0]["url"]}
        except Exception:
            pass

    # 3. UNIVERSAL RAPIDAPI ENGINE (Instagram, Facebook, Twitter, etc.)
    try:
        rapid_url = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        resp = requests.post(rapid_url, json={"url": url}, headers=headers, timeout=12)
        res_json = resp.json()

        direct_link = extract_url_from_json(res_json)
        if direct_link:
            return {"status": "success", "download_url": direct_link}
    except Exception as e:
        print(f"RapidAPI Error: {e}")

    raise HTTPException(status_code=400, detail="Extraction failed for this URL")
