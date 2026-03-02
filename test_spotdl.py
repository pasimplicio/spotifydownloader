import subprocess
import os
from pathlib import Path

print("🔍 Testando SpotDL...")

# Comando simples
cmd = [
    "spotdl",
    "https://open.spotify.com/intl-pt/track/2UsuUTVnFKR64iAhjWe9zn",
    "--format", "mp3",
]

print(f"Comando: {' '.join(cmd)}")

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    print(f"✅ Código de retorno: {result.returncode}")
    print(f"📤 STDOUT: {result.stdout[:500]}")
    print(f"📥 STDERR: {result.stderr[:500]}")

except Exception as e:
    print(f"❌ Erro: {e}")