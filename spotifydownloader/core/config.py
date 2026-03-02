import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

settings = Settings()

if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
    raise RuntimeError("Defina SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no .env")