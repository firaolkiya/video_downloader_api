from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from pytube import YouTube
import time
import re
from pytube.cli import on_progress

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
        max_retries = 10
        for attempt in range(max_retries):
            try:
                # Create YouTube object with progress callback
                yt = YouTube(
                    url,
                    on_progress_callback=on_progress,
                    use_oauth=False,
                    allow_oauth_cache=True
                )
                
                # Wait for the video info to be loaded
                time.sleep(1)
                
                # Try different stream options
                video_stream = None
                
                # Try progressive streams first
                streams = yt.streams.filter(progressive=True, file_extension='mp4')
                if streams:
                    video_stream = streams.order_by('resolution').desc().first()
                
                # If no progressive stream, try adaptive streams
                if not video_stream:
                    streams = yt.streams.filter(adaptive=True, file_extension='mp4')
                    if streams:
                        video_stream = streams.order_by('resolution').desc().first()
                
                # If still no stream, try any MP4 stream
                if not video_stream:
                    streams = yt.streams.filter(file_extension='mp4')
                    if streams:
                        video_stream = streams.order_by('resolution').desc().first()
                
                if not video_stream:
                    raise HTTPException(status_code=400, detail="No suitable video stream found")

                # Download the video
                print(f"Downloading video: {yt.title}")
                video_stream.download(output_path=DOWNLOAD_DIR, filename=f"{unique_id}.mp4")
                print("Download completed")
                break
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Failed to download video after {max_retries} attempts: {str(e)}")
                time.sleep(2)  # Wait longer between retries

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
