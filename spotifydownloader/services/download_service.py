import base64
import httpx
from spotifydownloader.core.config import settings


class SpotifyService:

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    TRACK_URL = "https://api.spotify.com/v1/tracks/{}"

    async def get_access_token(self) -> str:
        auth = base64.b64encode(
            f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "client_credentials"},
            )

        response.raise_for_status()
        return response.json()["access_token"]

    async def get_track(self, track_id: str) -> dict:
        token = await self.get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.TRACK_URL.format(track_id),
                headers={"Authorization": f"Bearer {token}"},
            )

        response.raise_for_status()
        return response.json()