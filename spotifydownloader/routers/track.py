print(">>> TRACK ROUTER DEFINITIVO <<<")

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/")
async def home():
    return HTMLResponse("<h1>HOME OK</h1>")

@router.post("/search")
async def search():
    return HTMLResponse("<h1>SEARCH EXECUTADO</h1>")