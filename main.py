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

# RAPIDAPI CREDENTIALS (FROM YOUR SCREENSHOT)
RAPIDAPI_KEY = "fe64982d69msh9912a3389f014cfp15b50bjsn7c1175c1ff2d"
RAPIDAPI_HOST = "auto-download-all-in-one-big.p.rapidapi.com"

@app.get("/")
def read_root():
    return {"message": "GM Social Downloader RapidAPI Engine Active!"}

@app.post("/extract")
def extract_video_info(data: VideoRequest):
    input_url = data.url.strip()

    endpoint = f"https://{RAPIDAPI_HOST}/v1/social/autolink"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    payload = {"url": input_url}

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        res_data = response.json()

        # Parse response logic
        if response.status_code == 200:
            # 1. If response contains 'medias' array
            if "medias" in res_data and isinstance(res_data["medias"], list) and len(res_data["medias"]) > 0:
                # Get the highest quality / first link
                dl_link = res_data["medias"][0].get("url")
                if dl_link:
                    return {"status": "success", "download_url": dl_link}

            # 2. Direct url parameters check
            if "url" in res_data and res_data["url"]:
                return {"status": "success", "download_url": res_data["url"]}
                
            if "download_url" in res_data and res_data["download_url"]:
                return {"status": "success", "download_url": res_data["download_url"]}

        # If API returned an error message
        error_msg = res_data.get("message", "Unable to extract download link.")
        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
