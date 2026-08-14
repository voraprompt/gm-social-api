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

def find_mp4_in_dict(obj):
    """Recursively search for any valid video URL in JSON response"""
    if isinstance(obj, str):
        if obj.startswith("http") and (".mp4" in obj.lower() or "googlevideo.com" in obj.lower() or "cdn" in obj.lower() or "tiktok" in obj.lower()):
            return obj
    elif isinstance(obj, list):
        for item in obj:
            res = find_mp4_in_dict(item)
            if res:
                return res
    elif isinstance(obj, dict):
        # Priority keys check
        for priority_key in ["url", "download_url", "link", "play"]:
            if priority_key in obj and isinstance(obj[priority_key], str) and obj[priority_key].startswith("http"):
                return obj[priority_key]
        for k, v in obj.items():
            res = find_mp4_in_dict(v)
            if res:
                return res
    return None

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader Backend Active!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    input_url = data.url.strip()

    if not input_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # 1. TIKTOK DIRECT ENGINE (Fastest & Guaranteed No-Watermark)
    if "tiktok.com" in input_url:
        try:
            tikwm_res = requests.post("https://www.tikwm.com/api/", data={"url": input_url}, timeout=8).json()
            if tikwm_res.get("code") == 0 and "play" in tikwm_res.get("data", {}):
                dl = tikwm_res["data"]["play"]
                if not dl.startswith("http"):
                    dl = "https://www.tikwm.com" + dl
                return {"status": "success", "download_url": dl}
        except Exception:
            pass

    # 2. RAPIDAPI UNIVERSAL EXTRACTION ENGINE
    try:
        endpoint = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, json={"url": input_url}, headers=headers, timeout=12)
        res_data = response.json()

        # Recursive link finder in RapidAPI JSON
        found_url = find_mp4_in_dict(res_data)
        if found_url:
            return {"status": "success", "download_url": found_url}
            
        # If RapidAPI returned an error object/msg
        if "message" in res_data:
            rapid_msg = res_data["message"]
        else:
            rapid_msg = str(res_data)[:100]

    except Exception as e:
        rapid_msg = str(e)

    # 3. YOUTUBE FALLBACK ENGINE (Invidious Direct Mirror)
    if "youtube.com" in input_url or "youtu.be" in input_url:
        try:
            video_id = ""
            if "shorts/" in input_url:
                video_id = input_url.split("shorts/")[1].split("?")[0].split("/")[0]
            elif "v=" in input_url:
                video_id = input_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in input_url:
                video_id = input_url.split("youtu.be/")[1].split("?")[0]

            if video_id:
                inv_res = requests.get(f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}", timeout=8).json()
                streams = inv_res.get("formatStreams", [])
                if streams and len(streams) > 0:
                    return {"status": "success", "download_url": streams[0]["url"]}
        except Exception:
            pass

    # If all engines fail, show exact reason instead of generic error
    raise HTTPException(status_code=400, detail=f"API Error: {rapid_msg}")
