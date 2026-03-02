from fastapi import FastAPI
from spotifydownloader.routers import track_router, download_completo_router

app = FastAPI(title="Spotify Downloader - Preview + Completo")

# Inclui os routers
app.include_router(track_router)
app.include_router(download_completo_router)

@app.get("/")
async def root():
    return {"message": "Spotify Downloader API",
            "endpoints": {
                "preview": "/ (página principal)",
                "download_completo": "/download-completo"
            }}