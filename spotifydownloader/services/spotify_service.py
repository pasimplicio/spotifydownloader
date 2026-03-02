import base64
import time
import logging

import httpx

from spotifydownloader.core.config import settings, validate_spotify_credentials

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpotifyService:
    """Serviço para interagir com a API do Spotify."""

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    TRACK_URL = "https://api.spotify.com/v1/tracks/{}"

    def __init__(self):
        self._access_token = None
        self._expires_at = 0

    async def _request_new_token(self) -> None:
        """Solicita um novo token de acesso ao Spotify."""
        try:
            validate_spotify_credentials()
        except RuntimeError as e:
            logger.error(f"Erro de validação: {e}")
            raise Exception("Credenciais do Spotify não configuradas. Verifique o arquivo .env")

        auth = base64.b64encode(
            f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={"Authorization": f"Basic {auth}"},
                    data={"grant_type": "client_credentials"},
                )
            except httpx.TimeoutException:
                logger.error("Timeout ao solicitar token do Spotify")
                raise Exception("Timeout ao conectar com o Spotify")
            except Exception as e:
                logger.error(f"Erro na requisição: {e}")
                raise Exception(f"Erro ao conectar com o Spotify: {e}")

        if response.status_code != 200:
            error_msg = f"Erro ao obter token do Spotify (status {response.status_code})"
            try:
                error_data = response.json()
                if "error_description" in error_data:
                    error_msg += f": {error_data['error_description']}"
            except:
                error_msg += f": {response.text}"

            logger.error(error_msg)
            raise Exception(error_msg)

        data = response.json()
        self._access_token = data["access_token"]
        # Renova 30 segundos antes de expirar
        self._expires_at = time.time() + data["expires_in"] - 30
        logger.info("Novo token obtido com sucesso")

    async def get_access_token(self) -> str:
        """Retorna um token de acesso válido."""
        if not self._access_token or time.time() >= self._expires_at:
            await self._request_new_token()
        return self._access_token

    async def get_track(self, track_id: str) -> dict:
        """
        Busca informações de uma faixa pelo ID.

        Args:
            track_id: ID da faixa do Spotify (22 caracteres)

        Returns:
            Dict com os dados da faixa
        """
        if not track_id or len(track_id) != 22:
            raise ValueError("ID de faixa inválido")

        token = await self.get_access_token()

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(
                    self.TRACK_URL.format(track_id),
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.TimeoutException:
                logger.error(f"Timeout ao buscar track {track_id}")
                raise Exception("Timeout ao consultar o Spotify")
            except Exception as e:
                logger.error(f"Erro na requisição: {e}")
                raise Exception(f"Erro ao conectar com o Spotify: {e}")

        if response.status_code == 404:
            logger.warning(f"Track {track_id} não encontrada")
            raise Exception("Faixa não encontrada no Spotify")
        elif response.status_code == 401:
            # Token expirado, tenta novamente com token novo
            logger.info("Token expirado, renovando...")
            self._access_token = None
            return await self.get_track(track_id)
        elif response.status_code != 200:
            error_msg = f"Spotify retornou erro {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_msg += f": {error_data['error']['message']}"
            except:
                error_msg += f": {response.text}"

            logger.error(error_msg)
            raise Exception(error_msg)

        return response.json()