from fastapi import FastAPI
from spotifydownloader.routers import track

app = FastAPI(title="Spotify Preview Downloader")

app.include_router(track.router)