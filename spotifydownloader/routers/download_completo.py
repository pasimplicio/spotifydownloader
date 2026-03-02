from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
import os

from spotifydownloader.services.download_alternativo import DownloadAlternativo

router = APIRouter(prefix="/download-completo")
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
downloader = DownloadAlternativo()

class DownloadRequest(BaseModel):
    url: str

@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    """Página principal"""
    return templates.TemplateResponse(
        "download_completo.html",
        {"request": request, "downloads": downloader.list_downloads()}
    )

@router.post("/download")
async def download(request: DownloadRequest):
    """Download via YouTube"""
    try:
        result = await downloader.download_from_youtube(request.url)
        if not result.get("success"):
            return JSONResponse(result, status_code=400)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@router.get("/list")
async def list_downloads():
    """Lista arquivos baixados"""
    return JSONResponse(downloader.list_downloads())

@router.get("/file/{filename}")
async def get_file(filename: str):
    """Download do arquivo"""
    file_path = downloader.download_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path=file_path, filename=filename, media_type="audio/mpeg")

@router.get("/folder")
async def open_folder():
    """Abre pasta de downloads"""
    try:
        os.startfile(str(downloader.download_path))
        return JSONResponse({"success": True})
    except:
        return JSONResponse({"success": False})

@router.post("/clear-cache")
async def clear_cache():
    """Limpa cache"""
    return JSONResponse({"success": downloader.clear_cache()})