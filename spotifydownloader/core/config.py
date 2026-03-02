import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


class Settings:
    """Configurações da aplicação."""

    # Spotify API
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    # Configurações do servidor
    APP_NAME: str = "Spotify Preview Downloader"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Timeouts
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))

    # URLs permitidas para download
    ALLOWED_DOMAINS: list = ["scdn.co", "p.scdn.co"]


settings = Settings()


def validate_spotify_credentials() -> None:
    """
    Valida se as credenciais do Spotify estão configuradas.

    Raises:
        RuntimeError: Se as credenciais não estiverem configuradas
    """
    if not settings.SPOTIFY_CLIENT_ID:
        raise RuntimeError("SPOTIFY_CLIENT_ID não configurado no arquivo .env")

    if not settings.SPOTIFY_CLIENT_SECRET:
        raise RuntimeError("SPOTIFY_CLIENT_SECRET não configurado no arquivo .env")