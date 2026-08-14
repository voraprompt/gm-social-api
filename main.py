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
    
    # 1. Resolve Redirects for Shortened URLs (like vt.tiktok.com)
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = session.head(input_url, allow_redirects=True, timeout=8, headers=headers)
        target_url = response.url
    except Exception:
        target_url = input_url

    # 2. Try Primary Extraction Engine (Cobalt v10 API)
    cobalt_endpoints = [
        "https://cobalt-api.kwippy.com",
        "https://api.cobalt.tools"
    ]
    
    for endpoint in cobalt_endpoints:
        try:
            cobalt_res = requests.post(
                endpoint,
                json={"url": target_url, "videoQuality": "720"},
                headers={"Accept": "application/json", "Content-Type": "application/json", **headers},
                timeout=10
            )
            res_data = cobalt_res.json()
            
            if "url" in res_data:
                return {"status": "success", "download_url": res_data["url"]}
            elif "picker" in res_data and len(res_data["picker"]) > 0:
                return {"status": "success", "download_url": res_data["picker"][0]["url"]}
        except Exception:
            continue

    # 3. Fallback Engine for TikTok & Reels (Tikwm / Direct Public Extractor)
    if "tiktok.com" in target_url:
        try:
            tikwm_res = requests.post("https://www.tikwm.com/api/", data={"url": target_url}, timeout=10).json()
            if tikwm_res.get("code") == 0 and "play" in tikwm_res.get("data", {}):
                dl_link = "https://www.tikwm.com" + tikwm_res["data"]["play"] if not tikwm_res["data"]["play"].startswith("http") else tikwm_res["data"]["play"]
                return {"status": "success", "download_url": dl_link}
        except Exception:
            pass

    raise HTTPException(status_code=400, detail="Failed to extract video. Service temporary unavailable.")
