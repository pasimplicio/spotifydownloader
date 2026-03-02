from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import re
import uvicorn

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="spotifydownloader/templates")


def extract_track_id(raw_url: str) -> str | None:
    if not raw_url:
        return None
    value = raw_url.strip().split('?')[0]
    match = re.search(r'[A-Za-z0-9]{22}', value)
    return match.group(0) if match else None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test-id")
async def test_id(url: str):
    track_id = extract_track_id(url)
    return JSONResponse({
        "url": url,
        "id": track_id,
        "valido": track_id is not None
    })


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, url: str = Form(...)):
    track_id = extract_track_id(url)
    if not track_id:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "URL inválida"}
        )

    # Mock de dados para teste
    data = {
        "name": "Música Teste",
        "artists": "Artista Teste",
        "album": "Álbum Teste",
        "cover": None,
        "preview": None
    }

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": data}
    )


if __name__ == "__main__":
    print("🚀 Servidor iniciando em http://127.0.0.1:8000")
    print("📝 Teste: http://127.0.0.1:8000/test-id?url=https://open.spotify.com/track/123")
    uvicorn.run(app, host="127.0.0.1", port=8000)