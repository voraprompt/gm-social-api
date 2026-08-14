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
    return {"message": "GM Social Downloader API is Active!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    input_url = data.url.strip()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # 1. TIKTOK DIRECT ENGINE
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

    # 2. YOUTUBE & INSTAGRAM COBALT ENGINE ROTATION
    instances = [
        "https://cobalt-api.kwippy.com",
        "https://api.cobalt.tools",
        "https://co.wuk.sh/api/json"
    ]

    for instance in instances:
        try:
            payload = {
                "url": input_url,
                "videoQuality": "720",
                "youtubeVideoCodec": "h264"
            }
            res = requests.post(instance, json=payload, headers=headers, timeout=10).json()
            
            if "url" in res:
                return {"status": "success", "download_url": res["url"]}
            elif "picker" in res and len(res["picker"]) > 0:
                return {"status": "success", "download_url": res["picker"][0]["url"]}
        except Exception:
            continue

    raise HTTPException(status_code=400, detail="Could not extract video. Public nodes busy, please try again.")
