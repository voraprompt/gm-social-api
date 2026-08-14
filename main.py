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
    # Free Open-Source Cobalt Engine Instance API
    cobalt_api_url = "https://co.wuk.sh/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": data.url,
        "vQuality": "max"
    }
    
    try:
        response = requests.post(cobalt_api_url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        
        # Check if cobalt returned valid video URL
        if "url" in res_data:
            return {
                "status": "success",
                "download_url": res_data["url"]
            }
        elif "picker" in res_data and len(res_data["picker"]) > 0:
            # For gallery/photo posts
            return {
                "status": "success",
                "download_url": res_data["picker"][0]["url"]
            }
        else:
            raise HTTPException(status_code=400, detail="Could not extract video link.")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
