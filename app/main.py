from fastapi import FastAPI, HTTPException
from pytube import YouTube

app = FastAPI()

@app.get("/download")
async def download_video(url: str):
    try:
        yt = YouTube(url)

        stream = yt.streams.get_highest_resolution()

        stream.download()

        return {"message": "Video downloaded successfully!"}
    except KeyError:
        raise HTTPException(status_code=400, detail="Error: Video is not available or cannot be downloaded")
    except ValueError:
        raise HTTPException(status_code=400, detail="Error: Invalid URL")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error downloading video: " + str(e))