import asyncio
import os
import json
from pathlib import Path
import re
from typing import Optional, Dict, Any, List
import subprocess
import shutil
from datetime import datetime
import sys

# FORÇAR FFMPEG LOCAL ANTES DE QUALQUER COISA
ffmpeg_local = Path.cwd() / "ffmpeg" / "bin"
if ffmpeg_local.exists():
    os.environ["PATH"] = str(ffmpeg_local) + os.pathsep + os.environ.get("PATH", "")
    print(f"🔥 FFMPEG LOCAL FORÇADO: {ffmpeg_local}")

class SpotDLService:
    """Serviço para download de músicas completas via SpotDL"""

    def __init__(self):
        self.download_path = Path.cwd() / "downloads"
        self.download_path.mkdir(exist_ok=True)
        self.temp_path = self.download_path / "temp"
        self.temp_path.mkdir(exist_ok=True)

        # Log file para debug
        self.log_file = self.download_path / "spotdl_debug.log"

    def _log(self, message: str):
        """Registra mensagens de log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        print(f"🔍 SPOTDL DEBUG: {message}")  # Console

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def _find_spotdl(self) -> Optional[str]:
        """Encontra o caminho do spotdl com debug"""
        self._log("Procurando spotdl...")

        # Verifica se spotdl está no PATH
        spotdl_path = shutil.which("spotdl")
        if spotdl_path:
            self._log(f"Spotdl encontrado no PATH: {spotdl_path}")
            return spotdl_path

        # Caminhos comuns
        common_paths = [
            str(Path.cwd() / ".venv" / "Scripts" / "spotdl.exe"),
            str(Path.cwd() / "Scripts" / "spotdl.exe"),
            str(Path.home() / ".local" / "bin" / "spotdl"),
            "C:\\Python311\\Scripts\\spotdl.exe",
        ]

        for path in common_paths:
            self._log(f"Verificando: {path}")
            if Path(path).exists():
                self._log(f"Spotdl encontrado em: {path}")
                return path

        # Tenta encontrar executáveis Python
        python_path = sys.executable
        python_dir = Path(python_path).parent
        possible_spotdl = python_dir / "spotdl.exe"

        if possible_spotdl.exists():
            self._log(f"Spotdl encontrado junto ao Python: {possible_spotdl}")
            return str(possible_spotdl)

        self._log("❌ Spotdl NÃO encontrado")
        return None

    def extract_track_info(self, url: str) -> Dict[str, Any]:
        """Extrai informações básicas da URL"""
        self._log(f"Extraindo informações da URL: {url}")

        # Padrões para IDs do Spotify
        track_pattern = r'(?:track[/:])([A-Za-z0-9]{22})'
        album_pattern = r'(?:album[/:])([A-Za-z0-9]{22})'
        playlist_pattern = r'(?:playlist[/:])([A-Za-z0-9]{22})'

        # Limpa a URL
        url = url.split('?')[0]
        self._log(f"URL limpa: {url}")

        track_match = re.search(track_pattern, url)
        album_match = re.search(album_pattern, url)
        playlist_match = re.search(playlist_pattern, url)

        if track_match:
            track_id = track_match.group(1)
            self._log(f"✅ ID de música encontrado: {track_id}")
            return {
                "type": "track",
                "id": track_id,
                "url": url,
                "name": "Música"
            }
        elif album_match:
            album_id = album_match.group(1)
            self._log(f"✅ ID de álbum encontrado: {album_id}")
            return {
                "type": "album",
                "id": album_id,
                "url": url,
                "name": "Álbum"
            }
        elif playlist_match:
            playlist_id = playlist_match.group(1)
            self._log(f"✅ ID de playlist encontrado: {playlist_id}")
            return {
                "type": "playlist",
                "id": playlist_id,
                "url": url,
                "name": "Playlist"
            }
        else:
            # Tenta extrair qualquer ID de 22 caracteres
            id_match = re.search(r'([A-Za-z0-9]{22})', url)
            if id_match:
                track_id = id_match.group(1)
                self._log(f"✅ ID encontrado por busca geral: {track_id}")
                return {
                    "type": "track",
                    "id": track_id,
                    "url": url,
                    "name": "Música"
                }

            self._log(f"❌ Nenhum ID encontrado na URL: {url}")
            raise ValueError("URL do Spotify inválida")

    async def download_track(self, url: str) -> Dict[str, Any]:
        """Download de uma música via SpotDL"""
        self._log(f"\n{'=' * 50}")
        self._log(f"Iniciando download para: {url}")

        try:
            # Encontra spotdl
            spotdl_path = self._find_spotdl()
            if not spotdl_path:
                error_msg = "SpotDL não encontrado. Execute: pip install spotdl"
                self._log(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "missing_spotdl"
                }

            # Verifica se há credenciais
            client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
            client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")

            if client_id and client_secret:
                self._log("✅ Credenciais encontradas no .env")
            else:
                self._log("⚠️ Sem credenciais no .env - pode haver rate limit")

            # Prepara o comando - VERSÃO SIMPLIFICADA
            cmd = [
                spotdl_path,
                url,
                "--output", str(self.download_path / "{artist} - {title}.{ext}"),
                "--format", "mp3",
                "--quality", "320k",
            ]

            # Adiciona credenciais se existirem
            if client_id and client_secret:
                cmd.extend(["--client-id", client_id])
                cmd.extend(["--client-secret", client_secret])

            self._log(f"Comando: {' '.join(cmd)}")

            # Executa o comando
            self._log("Executando spotdl...")

            # Usar subprocess diretamente para melhor debug
            import subprocess

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    cwd=str(self.download_path)
                )

                stdout_str = result.stdout
                stderr_str = result.stderr

                self._log(f"STDOUT: {stdout_str[:500]}")
                self._log(f"STDERR: {stderr_str[:500]}")
                self._log(f"Código de retorno: {result.returncode}")

                if result.returncode != 0:
                    error_msg = stderr_str if stderr_str else "Erro desconhecido"

                    # Trata erros comuns
                    if "rate limit" in error_msg.lower():
                        return {
                            "success": False,
                            "error": "Limite de requisições atingido. Tente novamente mais tarde.",
                            "error_type": "rate_limit",
                            "details": error_msg[:200]
                        }
                    elif "ffmpeg" in error_msg.lower():
                        return {
                            "success": False,
                            "error": "FFmpeg não encontrado. Instale: https://ffmpeg.org/download.html",
                            "error_type": "missing_ffmpeg",
                            "details": error_msg[:200]
                        }
                    elif "No items found" in error_msg:
                        return {
                            "success": False,
                            "error": "Música não encontrada no Spotify",
                            "error_type": "not_found"
                        }
                    elif "No module named" in error_msg:
                        return {
                            "success": False,
                            "error": "Erro de dependência do SpotDL. Execute: pip install --upgrade spotdl yt-dlp",
                            "error_type": "missing_deps",
                            "details": error_msg[:200]
                        }

                    return {
                        "success": False,
                        "error": f"Erro no download: {error_msg[:200]}",
                        "error_type": "unknown",
                        "details": error_msg[:500]
                    }

            except subprocess.TimeoutExpired:
                self._log("❌ Timeout após 3 minutos")
                return {
                    "success": False,
                    "error": "Timeout: download muito demorado (mais de 3 minutos)",
                    "error_type": "timeout"
                }
            except Exception as e:
                self._log(f"❌ Erro na execução: {str(e)}")
                return {
                    "success": False,
                    "error": f"Erro na execução: {str(e)}",
                    "error_type": "execution_error"
                }

            # Procura o arquivo mais recente
            self._log("Download concluído, procurando arquivo...")
            mp3_files = list(self.download_path.glob("*.mp3"))

            if mp3_files:
                newest_file = max(mp3_files, key=lambda f: f.stat().st_mtime)
                file_size = newest_file.stat().st_size
                size_mb = file_size / (1024 * 1024)

                self._log(f"✅ Arquivo encontrado: {newest_file.name} ({size_mb:.2f} MB)")

                return {
                    "success": True,
                    "file": str(newest_file),
                    "filename": newest_file.name,
                    "size": file_size,
                    "size_mb": round(size_mb, 2),
                    "path": f"/download-completo/file/{newest_file.name}"
                }
            else:
                self._log("⚠️ Download concluído mas nenhum arquivo MP3 encontrado")
                return {
                    "success": True,
                    "message": "Download concluído, mas arquivo não encontrado",
                    "warning": "O spotdl pode ter salvo em outro formato"
                }

        except Exception as e:
            self._log(f"❌ Exceção: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "error_type": "exception",
                "traceback": traceback.format_exc()
            }

    def list_downloads(self) -> List[Dict[str, Any]]:
        """Lista os arquivos baixados"""
        files = []
        for file in self.download_path.glob("*.mp3"):
            stats = file.stat()
            files.append({
                "name": file.name,
                "path": str(file),
                "size": stats.st_size,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "modified": stats.st_mtime,
                "modified_str": datetime.fromtimestamp(stats.st_mtime).strftime("%d/%m/%Y %H:%M")
            })

        # Ordena por data (mais recente primeiro)
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def get_download_path(self) -> str:
        """Retorna o caminho da pasta de downloads"""
        return str(self.download_path)

    def get_log_content(self) -> str:
        """Retorna o conteúdo do log"""
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.read()
        return "Log não encontrado"