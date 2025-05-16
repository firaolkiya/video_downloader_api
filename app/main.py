from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from pytube import YouTube
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
        yt = YouTube(url)
        
        stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
        
        if not stream:
            return JSONResponse(status_code=404, content={"error": "No MP4 stream available for this video."})
        
        video_filename = f"{uuid.uuid4()}.mp4"
        video_filepath = os.path.join(DOWNLOAD_DIR, video_filename)
        stream.download(output_path=DOWNLOAD_DIR, filename=video_filename)
        
        return FileResponse(video_filepath, media_type="video/mp4", filename=f"{yt.title}.mp4")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})