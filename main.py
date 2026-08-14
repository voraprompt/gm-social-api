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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # 1. SPECIAL YOUTUBE ENGINE FALLBACK (Bypasses YouTube Sign-in / Bot Block)
    if "youtube.com" in input_url or "youtu.be" in input_url:
        try:
            # YouTube specific API endpoint
            yt_api_url = "https://api.cobalt.tools"
            yt_payload = {
                "url": input_url,
                "videoQuality": "720",
                "youtubeVideoCodec": "h264"
            }
            res = requests.post(yt_api_url, json=yt_payload, headers=headers, timeout=12).json()
            if "url" in res:
                return {"status": "success", "download_url": res["url"]}
        except Exception:
            pass

        # Second YouTube API Engine Fallback
        try:
            y2_res = requests.post(
                "https://co.wuk.sh/api/json",
                json={"url": input_url, "vQuality": "720"},
                headers=headers,
                timeout=12
            ).json()
            if "url" in y2_res:
                return {"status": "success", "download_url": y2_res["url"]}
        except Exception:
            pass

    # 2. TIKTOK SPECIAL FALLBACK
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

    # 3. INSTAGRAM / GENERAL SOCIAL MEDIA ENGINE
    try:
        general_res = requests.post(
            "https://cobalt-api.kwippy.com",
            json={"url": input_url},
            headers=headers,
            timeout=12
        ).json()
        
        if "url" in general_res:
            return {"status": "success", "download_url": general_res["url"]}
        elif "picker" in general_res and len(general_res["picker"]) > 0:
            return {"status": "success", "download_url": general_res["picker"][0]["url"]}
    except Exception:
        pass

    raise HTTPException(status_code=400, detail="Could not extract media. Please try another link.")
