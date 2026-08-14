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

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader API is Running!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    input_url = data.url.strip()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # 1. TIKTOK ENGINE (100% Free & Fast - TikWM Engine)
    if "tiktok.com" in input_url:
        try:
            tikwm_res = requests.post("https://www.tikwm.com/api/", data={"url": input_url}, timeout=10).json()
            if tikwm_res.get("code") == 0 and "play" in tikwm_res.get("data", {}):
                dl_link = tikwm_res["data"]["play"]
                if not dl_link.startswith("http"):
                    dl_link = "https://www.tikwm.com" + dl_link
                return {"status": "success", "download_url": dl_link}
        except Exception as e:
            print(f"TikTok Extraction Error: {e}")

    # 2. YOUTUBE & INSTAGRAM MULTI-ENGINE
    # Public Multi-Engine API Endpoint (No Block / Auto-Proxy Handling)
    try:
        response = requests.get(
            f"https://api.vytal.dev/v1/extract?url={input_url}",
            headers=headers,
            timeout=12
        )
        if response.status_code == 200:
            res_json = response.json()
            if "download_url" in res_json:
                return {"status": "success", "download_url": res_json["download_url"]}
            elif "url" in res_json:
                return {"status": "success", "download_url": res_json["url"]}
    except Exception:
        pass

    # 3. YOUTUBE DIRECT FALLBACK ENGINE
    if "youtube.com" in input_url or "youtu.be" in input_url:
        try:
            # Free Invidious Public Instance Engine
            invidious_res = requests.get(
                f"https://api.invidious.io/v1/videos/{input_url.split('/')[-1]}",
                timeout=10
            ).json()
            
            format_streams = invidious_res.get("formatStreams", [])
            if format_streams:
                return {"status": "success", "download_url": format_streams[0]["url"]}
        except Exception:
            pass

    raise HTTPException(status_code=400, detail="Could not extract video link. Server IP blocked by provider.")
