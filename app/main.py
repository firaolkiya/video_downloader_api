from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from pytube import YouTube
import time
import re

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

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:embed\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.post("/download/")
async def download_youtube_video(url: str = Query(..., description="The YouTube video URL")):
    output_path = None
    try:
        # Validate and extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Create a unique filename
        unique_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp4")

        # Initialize YouTube object with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                yt = YouTube(
                    url,
                    use_oauth=False,
                    allow_oauth_cache=True
                )
                
                # Get the highest resolution stream
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                
                if not video_stream:
                    # Try without progressive filter if no progressive stream is found
                    video_stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()
                
                if not video_stream:
                    raise HTTPException(status_code=400, detail="No suitable video stream found")

                # Download the video
                video_stream.download(output_path=DOWNLOAD_DIR, filename=f"{unique_id}.mp4")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Failed to download video after {max_retries} attempts: {str(e)}")
                time.sleep(1)  # Wait before retrying

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

    except HTTPException as he:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        raise he
    except Exception as e:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        return JSONResponse(status_code=500, content={"error": str(e)})
