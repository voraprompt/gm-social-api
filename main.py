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

def unshorten_url(url: str) -> str:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5)
        return resp.url
    except Exception:
        return url

def search_json(data):
    if isinstance(data, str) and data.startswith("http"):
        if any(ext in data.lower() for ext in [".mp4", "googlevideo", "tiktokcdn"]):
            return data
    elif isinstance(data, dict):
        for k in ["url", "download_url", "play", "no_watermark", "link"]:
            if k in data and isinstance(data[k], str) and data[k].startswith("http"):
                return data[k]
        for v in data.values():
            res = search_json(v)
            if res: return res
    elif isinstance(data, list):
        for item in data:
            res = search_json(item)
            if res: return res
    return None

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader API Active!"}

@app.post("/extract")
def extract_video(req: VideoRequest):
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL is empty")

    target_url = unshorten_url(raw_url)

    # TikTok Engine
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

    # Universal RapidAPI Engine (Youtube, Insta, FB, etc)
    try:
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        resp = requests.post(f"https://{RAPIDAPI_HOST}/v1/social/autolink", json={"url": target_url}, headers=headers, timeout=12)
        if resp.status_code == 200:
            media = search_json(resp.json())
            if media:
                return {"status": "success", "download_url": media}
    except Exception:
        pass

    raise HTTPException(status_code=400, detail="Extraction failed for this URL")
