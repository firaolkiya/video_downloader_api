from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from yt_dlp import YoutubeDL
import shutil
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
        video_id = str(uuid.uuid4())
        filepath_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")

        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': filepath_template,
            'quiet': True,
            'cookiefile': 'youtube_cookies.txt',
            'no_warnings': True,
            'extract_flat': False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=True)
                if not info_dict:
                    raise HTTPException(status_code=400, detail="Could not extract video information")
                
                final_filepath = filepath_template.replace("%(ext)s", "mp4")
                
                if not os.path.exists(final_filepath):
                    raise HTTPException(status_code=500, detail="Video download failed")

                # Get video title and sanitize it for filename
                video_title = info_dict.get('title', video_id)
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]  # Limit length
                
                # Create a temporary copy with the proper name
                temp_filepath = os.path.join(DOWNLOAD_DIR, f"{safe_title}.mp4")
                shutil.copy2(final_filepath, temp_filepath)

                # Clean up the original file
                os.remove(final_filepath)

                # Return the file as a streaming response
                return FileResponse(
                    temp_filepath,
                    media_type="video/mp4",
                    filename=f"{safe_title}.mp4",
                    background=cleanup_old_files
                )

            except Exception as e:
                if os.path.exists(final_filepath):
                    os.remove(final_filepath)
                raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
