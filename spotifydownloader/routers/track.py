import re
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from spotifydownloader.services.spotify_service import SpotifyService
from spotifydownloader.services.download_service import download_preview_audio

# Cria o router com prefixo vazio para garantir
router = APIRouter(prefix="", tags=["spotify"])

spotify_service = SpotifyService()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def extract_track_id(raw_url: str) -> str | None:
    """Extrai o ID da faixa de diferentes formatos de URL do Spotify."""
    if not raw_url:
        return None

    # Limpeza básica
    value = raw_url.strip()
    value = value.split('?')[0]  # Remove query parameters

    # Padrão para IDs do Spotify (22 caracteres alfanuméricos)
    SPOTIFY_ID_PATTERN = r'^[A-Za-z0-9]{22}$'

    # CASO 1: Já é um ID direto
    if re.match(SPOTIFY_ID_PATTERN, value):
        return value

    # CASO 2: Formato spotify:track:ID
    if "spotify:track:" in value:
        track_id = value.split("spotify:track:")[-1]
        if re.match(SPOTIFY_ID_PATTERN, track_id):
            return track_id

    # CASO 3: URL do Spotify
    parts = value.split('/')
    for part in parts:
        if len(part) == 22 and part.isalnum():
            return part

    # CASO 4: Busca por qualquer padrão de 22 caracteres
    match = re.search(r'[A-Za-z0-9]{22}', value)
    if match:
        return match.group(0)

    return None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": None,
            "error": None,
            "debug": None
        }
    )


@router.get("/test-id", response_class=JSONResponse)
async def test_id(url: str):
    """Rota de teste para extrair ID"""
    track_id = extract_track_id(url)
    return {
        "sucesso": True,
        "url_recebida": url,
        "id_extraido": track_id,
        "valido": track_id is not None
    }


@router.post("/search", response_class=HTMLResponse)
async def search(request: Request, url: str = Form(...)):
    """Busca informações de uma faixa do Spotify"""
    debug_info = {
        "raw_url": url,
        "final_url": url.strip() if url else "",
        "track_id": "",
        "spotify_status": "não consultado",
        "error": ""
    }

    track_id = extract_track_id(url)
    debug_info["track_id"] = track_id or ""

    if not track_id:
        debug_info["error"] = "track_id não encontrado"
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "URL inválida. Use um link de faixa do Spotify",
                "data": None,
                "debug": debug_info,
            },
            status_code=400,
        )

    try:
        track = await spotify_service.get_track(track_id)
        debug_info["spotify_status"] = "ok"
    except Exception as exc:
        debug_info["spotify_status"] = "erro"
        debug_info["error"] = str(exc)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": f"Erro ao consultar Spotify: {exc}",
                "data": None,
                "debug": debug_info,
            },
            status_code=502,
        )

    data = {
        "name": track.get("name", "Sem título"),
        "artists": ", ".join(artist.get("name", "") for artist in track.get("artists", [])),
        "album": track.get("album", {}).get("name", ""),
        "cover": (track.get("album", {}).get("images") or [{}])[0].get("url") if track.get("album") else None,
        "preview": track.get("preview_url"),
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "error": None,
            "debug": debug_info,
        },
    )


@router.get("/download")
async def download(url: str = Query(..., min_length=1)):
    """Download do preview de áudio"""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de preview inválida")

    try:
        audio_bytes = await download_preview_audio(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha no download: {exc}") from exc

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="spotify_preview.mp3"'},
    )