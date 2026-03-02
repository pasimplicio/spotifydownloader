import subprocess

print("🔍 Testando yt-dlp...")

# yt-dlp pode baixar do Spotify também
cmd = [
    "yt-dlp",
    "--extract-audio",
    "--audio-format", "mp3",
    "--audio-quality", "0",
    "https://open.spotify.com/intl-pt/track/2UsuUTVnFKR64iAhjWe9zn"
]

print(f"Comando: {' '.join(cmd)}")

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120
    )

    print(f"✅ Código de retorno: {result.returncode}")
    print(f"📤 STDOUT: {result.stdout[:500]}")
    print(f"📥 STDERR: {result.stderr[:500]}")

except Exception as e:
    print(f"❌ Erro: {e}")