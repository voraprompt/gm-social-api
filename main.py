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

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader Backend Active!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    input_url = data.url.strip()

    # 1. Resolve TikTok Shortened Links (vt.tiktok.com)
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        resp = session.head(input_url, allow_redirects=True, timeout=8, headers=headers)
        target_url = resp.url
    except Exception:
        target_url = input_url

    # 2. TIKTOK DIRECT FALLBACK ENGINE (100% Reliable & Fast)
    if "tiktok.com" in target_url:
        try:
            tikwm_res = requests.post("https://www.tikwm.com/api/", data={"url": target_url}, timeout=10).json()
            if tikwm_res.get("code") == 0 and "play" in tikwm_res.get("data", {}):
                dl_link = tikwm_res["data"]["play"]
                if not dl_link.startswith("http"):
                    dl_link = "https://www.tikwm.com" + dl_link
                # Always return download_url directly
                return {"status": "success", "download_url": dl_link}
        except Exception:
            pass

    # 3. RAPIDAPI MULTI-DOWNLOADER (YouTube, Instagram, etc.)
    try:
        endpoint = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
        rapid_headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, json={"url": target_url}, headers=rapid_headers, timeout=12)
        res_data = response.json()

        if response.status_code == 200:
            if "medias" in res_data and len(res_data["medias"]) > 0:
                dl_link = res_data["medias"][0].get("url")
                if dl_link:
                    return {"status": "success", "download_url": dl_link}
            elif "url" in res_data and res_data["url"]:
                return {"status": "success", "download_url": res_data["url"]}
            elif "download_url" in res_data and res_data["download_url"]:
                return {"status": "success", "download_url": res_data["download_url"]}

    except Exception as e:
        print(f"RapidAPI Error: {e}")

    raise HTTPException(status_code=400, detail="Could not extract download link.")
