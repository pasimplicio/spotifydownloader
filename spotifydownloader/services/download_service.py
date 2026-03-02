import httpx


async def download_preview_audio(preview_url: str) -> bytes:
    """
    Download do preview de áudio do Spotify.

    Args:
        preview_url: URL do preview (geralmente de scdn.co)

    Returns:
        Bytes do arquivo de áudio

    Raises:
        ValueError: Se a URL for inválida
        Exception: Se o download falhar
    """
    if not preview_url or not preview_url.startswith(("http://", "https://")):
        raise ValueError("URL de preview inválida")

    async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
    ) as client:
        try:
            response = await client.get(preview_url)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise Exception("Timeout ao baixar o preview")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Erro HTTP {e.response.status_code} ao baixar preview")
        except Exception as e:
            raise Exception(f"Erro no download: {str(e)}")

    return response.content