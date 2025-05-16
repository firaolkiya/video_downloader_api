import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.post("/download/")
async def download_youtube_video(url: str = Query(..., description="The YouTube video URL")):
    try:
        video_id = str(uuid.uuid4())
        filepath = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
        
        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]",
            "-o", 
            
        filepath,
            url
        ]

        subprocess.run(cmd, check=True)

        return FileResponse(filepath, media_type="video/mp4", filename=f"{video_id}.mp4")
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": f"Download failed: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
