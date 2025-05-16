from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from yt_dlp import YoutubeDL

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
        filepath_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': filepath_template,
            'quiet': True,
            'cookiefile': 'youtube_cookies.txt',  # Add this line
        }


        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_filepath = filepath_template.replace("%(ext)s", "mp4")

        return FileResponse(final_filepath, media_type="video/mp4", filename=f"{info_dict.get('title', video_id)}.mp4")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
