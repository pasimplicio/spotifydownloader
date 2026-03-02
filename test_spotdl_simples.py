import subprocess
import time

print("🔍 Testando SpotDL com timeout maior...")

# Versão mais simples ainda
cmd = [
    "spotdl",
    "https://open.spotify.com/intl-pt/track/2UsuUTVnFKR64iAhjWe9zn"
]

print(f"Comando: {' '.join(cmd)}")
print("⏳ Aguardando até 5 minutos...")

try:
    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minutos
    )

    elapsed = time.time() - start_time
    print(f"✅ Tempo decorrido: {elapsed:.1f} segundos")
    print(f"✅ Código de retorno: {result.returncode}")

    if result.stdout:
        print(f"\n📤 STDOUT (primeiras 500 linhas):")
        print("-" * 50)
        print(result.stdout[:2000])
        print("-" * 50)

    if result.stderr:
        print(f"\n📥 STDERR:")
        print("-" * 50)
        print(result.stderr[:1000])
        print("-" * 50)

except subprocess.TimeoutExpired:
    print("❌ Timeout após 5 minutos")
except Exception as e:
    print(f"❌ Erro: {e}")