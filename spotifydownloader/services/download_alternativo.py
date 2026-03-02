"""
Serviço de download via YouTube - VERSÃO FINAL
Baixa músicas do YouTube com metadados corretos do Spotify
"""
import subprocess
import re
import requests
from pathlib import Path
from datetime import datetime
import shutil
import json
from bs4 import BeautifulSoup
import os
import time

class DownloadAlternativo:
    """Serviço de download via YouTube com metadados do Spotify"""

    def __init__(self):
        # Pastas do projeto
        self.download_path = Path.cwd() / "downloads"
        self.download_path.mkdir(exist_ok=True)

        # Cache para metadados
        self.cache_path = self.download_path / "cache"
        self.cache_path.mkdir(exist_ok=True)

        # FFmpeg local
        self.ffmpeg_path = Path.cwd() / "ffmpeg" / "bin" / "ffmpeg.exe"
        self.ffmpeg_dir = str(self.ffmpeg_path.parent)

        # Força FFmpeg no PATH
        if self.ffmpeg_path.exists():
            os.environ["PATH"] = self.ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            print(f"✅ FFmpeg pronto: {self.ffmpeg_path}")

        # Headers para requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _log(self, message: str):
        """Log simples"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"📥 [{timestamp}] {message}")

    def extract_track_id(self, url: str) -> str:
        """Extrai ID do Spotify da URL"""
        url = url.strip().split('?')[0]

        # Padrões de ID (22 caracteres)
        patterns = [
            r'track[/:]([A-Za-z0-9]{22})',
            r'([A-Za-z0-9]{22})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                track_id = match.group(1) if '(' in pattern else match.group(0)
                if len(track_id) == 22 and track_id.isalnum():
                    return track_id

        raise ValueError("URL inválida")

    async def get_spotify_metadata(self, track_id: str) -> dict:
        """
        Busca METADADOS REAIS do Spotify (nome do artista e música)
        """
        self._log(f"Buscando metadados para: {track_id}")

        # Verifica cache
        cache_file = self.cache_path / f"{track_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cache_time = datetime.fromtimestamp(cache_data.get('timestamp', 0))
                    if (datetime.now() - cache_time).days < 30:
                        self._log("✅ Usando cache")
                        return cache_data['metadata']
            except:
                pass

        # Tenta diferentes URLs
        urls = [
            f"https://open.spotify.com/track/{track_id}",
            f"https://open.spotify.com/intl-pt/track/{track_id}",
        ]

        metadata = {
            "name": "Música",
            "artists": "Artista",
            "album": "Álbum",
            "track_id": track_id,
            "search_query": ""  # Para busca no YouTube
        }

        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Tenta encontrar o título real da música
                    title_tag = soup.find("meta", property="og:title")
                    if title_tag:
                        full_title = title_tag.get("content", "")
                        self._log(f"Título bruto: {full_title}")

                        # Tenta separar artista da música
                        if " - " in full_title:
                            parts = full_title.split(" - ", 1)
                            metadata["artists"] = parts[0].strip()
                            metadata["name"] = parts[1].strip()
                        else:
                            metadata["name"] = full_title

                    # Tenta encontrar descrição com mais detalhes
                    desc_tag = soup.find("meta", property="og:description")
                    if desc_tag and metadata["artists"] == "Artista":
                        desc = desc_tag.get("content", "")
                        parts = desc.split("·")
                        if len(parts) >= 1:
                            metadata["artists"] = parts[0].strip()

                    # Se ainda não tem artista, tenta no título da página
                    if metadata["artists"] == "Artista":
                        title_tag = soup.find("title")
                        if title_tag:
                            page_title = title_tag.text
                            if " - " in page_title:
                                parts = page_title.split(" - ", 1)
                                metadata["artists"] = parts[0].strip()
                                metadata["name"] = parts[1].split("|")[0].strip()

                    self._log(f"✅ Artista: {metadata['artists']}")
                    self._log(f"✅ Música: {metadata['name']}")

                    # Cria query para busca no YouTube
                    metadata["search_query"] = f"{metadata['artists']} {metadata['name']} audio"

                    # Salva cache
                    try:
                        cache_data = {
                            'timestamp': datetime.now().timestamp(),
                            'metadata': metadata
                        }
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=2)
                    except:
                        pass

                    return metadata

            except Exception as e:
                self._log(f"Erro na URL {url}: {str(e)}")
                continue

        # Fallback: usa o ID como nome
        metadata["name"] = f"Track_{track_id[:8]}"
        metadata["search_query"] = f"spotify track {track_id}"
        return metadata

    async def search_youtube_best_match(self, artist: str, title: str) -> tuple[str | None, str | None]:
        """
        Busca no YouTube e retorna (URL_do_audio, título_do_vídeo)
        """
        # Múltiplas tentativas de busca
        queries = [
            f"{artist} - {title} official audio",
            f"{artist} - {title} audio",
            f"{artist} {title} full song",
            f"{artist} - {title}",
            f"{title} {artist}",
            f"{artist} {title} lyrics",
        ]

        for query in queries:
            self._log(f"Buscando: {query}")

            try:
                # Usa yt-dlp para buscar
                cmd = [
                    "yt-dlp",
                    f"ytsearch5:{query}",  # Busca 5 resultados
                    "--print", "%(title)s|%(url)s",  # Título e URL
                    "--format", "bestaudio",
                    "--no-playlist",
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=20
                )

                if result.returncode == 0 and result.stdout:
                    # Processa resultados
                    lines = result.stdout.strip().split('\n')
                    for line in lines[:3]:  # Verifica os 3 primeiros
                        if '|' in line:
                            video_title, video_url = line.split('|', 1)
                            video_title = video_title.strip()
                            video_url = video_url.strip()

                            self._log(f"Encontrado: {video_title[:50]}...")

                            # Verifica se o título parece relevante
                            video_title_lower = video_title.lower()
                            artist_lower = artist.lower()
                            title_lower = title.lower()

                            # Pontuação de relevância
                            score = 0
                            if artist_lower in video_title_lower:
                                score += 2
                            if title_lower in video_title_lower:
                                score += 2
                            if "audio" in video_title_lower or "official" in video_title_lower:
                                score += 1
                            if "cover" in video_title_lower or "remix" in video_title_lower:
                                score -= 1

                            if score >= 2:  # Aceita se relevante
                                self._log(f"✅ Vídeo relevante encontrado (score {score})")
                                return video_url, video_title

            except Exception as e:
                self._log(f"Erro na busca: {e}")
                continue

        return None, None

    async def download_from_youtube(self, spotify_url: str) -> dict:
        """
        Download completo com metadados corretos
        """
        self._log(f"\n{'='*60}")
        self._log(f"Iniciando download: {spotify_url}")

        try:
            # Passo 1: Extrair ID
            track_id = self.extract_track_id(spotify_url)
            self._log(f"✅ ID: {track_id}")

            # Passo 2: Buscar metadados REAIS do Spotify
            metadata = await self.get_spotify_metadata(track_id)

            # Passo 3: Buscar no YouTube
            video_url, video_title = await self.search_youtube_best_match(
                metadata['artists'],
                metadata['name']
            )

            if not video_url:
                return {
                    "success": False,
                    "error": "Música não encontrada no YouTube"
                }

            # Passo 4: Preparar nome do arquivo (limpo)
            safe_artist = re.sub(r'[<>:"/\\|?*]', '', metadata['artists'])
            safe_title = re.sub(r'[<>:"/\\|?*]', '', metadata['name'])
            filename = f"{safe_artist} - {safe_title}.mp3"
            output_path = self.download_path / filename

            self._log(f"📁 Arquivo: {filename}")

            # Passo 5: Download e conversão
            cmd = [
                "yt-dlp",
                "-f", "bestaudio",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--embed-thumbnail",
                "--add-metadata",
                "--metadata", f"title={metadata['name']}",
                "--metadata", f"artist={metadata['artists']}",
                "--metadata", f"album={metadata['album']}",
                "--output", str(output_path),
                "--no-playlist",
                video_url
            ]

            self._log("⏳ Baixando...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                error = result.stderr if result.stderr else "Erro desconhecido"
                return {
                    "success": False,
                    "error": f"Falha: {error[:200]}"
                }

            # Verifica se o arquivo foi criado
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                self._log(f"✅ Sucesso! {filename} ({size_mb:.2f} MB)")

                return {
                    "success": True,
                    "file": str(output_path),
                    "filename": filename,
                    "size": output_path.stat().st_size,
                    "size_mb": round(size_mb, 2),
                    "path": f"/download-completo/file/{filename}",
                    "metadata": metadata
                }
            else:
                return {
                    "success": False,
                    "error": "Arquivo não encontrado após download"
                }

        except Exception as e:
            self._log(f"❌ Erro: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_downloads(self) -> list:
        """Lista arquivos baixados"""
        files = []
        for file in self.download_path.glob("*.mp3"):
            stats = file.stat()
            files.append({
                "name": file.name,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "modified": stats.st_mtime,
                "modified_str": datetime.fromtimestamp(stats.st_mtime).strftime("%d/%m/%Y %H:%M")
            })
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def clear_cache(self):
        """Limpa cache"""
        try:
            for file in self.cache_path.glob("*.json"):
                file.unlink()
            return True
        except:
            return False