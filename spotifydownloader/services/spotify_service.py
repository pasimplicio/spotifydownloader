import base64
import time
import httpx
from spotifydownloader.core.config import settings


class SpotifyService:

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    TRACK_URL = "https://api.spotify.com/v1/tracks/{}"

    def __init__(self):
        self._access_token = None
        self._expires_at = 0

    async def _request_new_token(self):
        auth = base64.b64encode(
            f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "client_credentials"},
            )

        if response.status_code != 200:
            print("TOKEN ERROR STATUS:", response.status_code)
            print("TOKEN ERROR BODY:", response.text)
            raise Exception("Erro ao obter token do Spotify")

        data = response.json()
        self._access_token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"] - 30

    async def get_access_token(self):
        if not self._access_token or time.time() >= self._expires_at:
            await self._request_new_token()
        return self._access_token

    async def get_track(self, track_id: str) -> dict:
        token = await self.get_access_token()

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                self.TRACK_URL.format(track_id),
                headers={"Authorization": f"Bearer {token}"},
            )

        if response.status_code != 200:
            print("TRACK ERROR STATUS:", response.status_code)
            print("TRACK ERROR BODY:", response.text)
            raise Exception(f"Spotify retornou erro {response.status_code}")

        return response.json()