from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from pytube import YouTube
import time

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

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    for filename in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.getmtime(filepath) < (time.time() - 3600):  # 1 hour
            try:
                os.remove(filepath)
            except:
                pass

@app.post("/download/")
async def download_youtube_video(url: str = Query(..., description="The YouTube video URL")):
    try:
        # Create a unique filename
        video_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

        # Initialize YouTube object
        yt = YouTube(url)
        
        # Get the highest resolution stream
        video_stream = yt.streams.get_highest_resolution()
        
        if not video_stream:
            raise HTTPException(status_code=400, detail="No suitable video stream found")

        # Download the video
        video_stream.download(output_path=DOWNLOAD_DIR, filename=f"{video_id}.mp4")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Video download failed")

        # Get video title and sanitize it
        video_title = yt.title
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]  # Limit length

        # Return the file
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"{safe_title}.mp4",
            background=cleanup_old_files
        )

    except Exception as e:
        # Clean up the file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        return JSONResponse(status_code=500, content={"error": str(e)})
