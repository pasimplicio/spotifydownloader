@echo off
echo Corrigindo estrutura completa do projeto...

REM Criar pasta do pacote principal se nao existir
if not exist spotifydownloader (
    mkdir spotifydownloader
)

REM Mover pastas para dentro do pacote
if exist core (
    move core spotifydownloader\
)

if exist routers (
    move routers spotifydownloader\
)

if exist services (
    move services spotifydownloader\
)

if exist templates (
    move templates spotifydownloader\
)

REM Mover main.py se estiver na raiz
if exist main.py (
    move main.py spotifydownloader\
)

REM Garantir __init__.py
if not exist spotifydownloader\__init__.py (
    type nul > spotifydownloader\__init__.py
)

echo Estrutura corrigida com sucesso!
echo.
echo Agora execute:
echo uvicorn spotifydownloader.main:app --reload
pause