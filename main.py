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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    # 1. TIKTOK ENGINE (100% Free - No Key/Card Needed)
    if "tiktok.com" in input_url:
        try:
            tikwm_res = requests.post("https://www.tikwm.com/api/", data={"url": input_url}, timeout=10).json()
            if tikwm_res.get("code") == 0 and "play" in tikwm_res.get("data", {}):
                dl_link = tikwm_res["data"]["play"]
                if not dl_link.startswith("http"):
                    dl_link = "https://www.tikwm.com" + dl_link
                return {"status": "success", "download_url": dl_link}
        except Exception:
            pass

    # 2. YOUTUBE ENGINE (Free Invidious API Mirror Engine - Bypasses Bot Check)
    if "youtube.com" in input_url or "youtu.be" in input_url:
        # Extract video ID
        video_id = ""
        if "shorts/" in input_url:
            video_id = input_url.split("shorts/")[1].split("?")[0].split("/")[0]
        elif "v=" in input_url:
            video_id = input_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in input_url:
            video_id = input_url.split("youtu.be/")[1].split("?")[0]

        if video_id:
            invidious_instances = [
                f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}",
                f"https://inv.tux.stream/api/v1/videos/{video_id}",
                f"https://invidious.drgns.space/api/v1/videos/{video_id}"
            ]
            
            for inst in invidious_instances:
                try:
                    res = requests.get(inst, headers=headers, timeout=8).json()
                    format_streams = res.get("formatStreams", [])
                    if format_streams:
                        # Grab highest quality video URL
                        return {"status": "success", "download_url": format_streams[0]["url"]}
                except Exception:
                    continue

    # 3. INSTAGRAM & GENERAL SOCIAL MEDIA (Cobalt API Open Mirrors)
    cobalt_mirrors = [
        "https://api.cobalt.tools",
        "https://cobalt-api.kwippy.com"
    ]
    
    for mirror in cobalt_mirrors:
        try:
            res = requests.post(
                mirror,
                json={"url": input_url, "videoQuality": "720"},
                headers={"Accept": "application/json", "Content-Type": "application/json", **headers},
                timeout=10
            ).json()
            
            if "url" in res:
                return {"status": "success", "download_url": res["url"]}
            elif "picker" in res and len(res["picker"]) > 0:
                return {"status": "success", "download_url": res["picker"][0]["url"]}
        except Exception:
            continue

    raise HTTPException(status_code=400, detail="Could not extract video. Please try again.")
