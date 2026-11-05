@echo off
chcp 65001 > nul
setlocal

echo ==============================================================
echo       Jack Bros VB Translation Tool - Demarrage
echo ==============================================================
echo.

REM --- Le port 8000 est-il deja pris ? ---------------------------------
REM L'ancienne version tuait d'office tout processus ecoutant sur 8000,
REM y compris un serveur de developpement sans rapport. On demande.
set "PID_OCCUPANT="
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do set "PID_OCCUPANT=%%a"

if defined PID_OCCUPANT (
    echo Le port 8000 est deja utilise par le processus %PID_OCCUPANT% :
    tasklist /FI "PID eq %PID_OCCUPANT%" /FO LIST | find "Nom" 2>nul
    tasklist /FI "PID eq %PID_OCCUPANT%" /FO LIST | find "Image" 2>nul
    echo.
    choice /C ON /N /M "Faut-il l'arreter ? [O]ui / [N]on (annule le demarrage) : "
    if errorlevel 2 (
        echo Demarrage annule. Liberez le port 8000, puis relancez.
        pause
        exit /b 1
    )
    taskkill /F /PID %PID_OCCUPANT% >nul 2>&1
    echo Processus %PID_OCCUPANT% arrete.
    echo.
)

echo Verification des dependances Python...
python -m pip install -r "%~dp0tool\requirements.txt" --quiet
if errorlevel 1 (
    echo.
    echo Echec de l'installation des dependances.
    echo Python est-il installe et accessible depuis le PATH ?
    pause
    exit /b 1
)

echo.
echo Lancement du serveur sur http://127.0.0.1:8000 ...
cd /d "%~dp0"
python tool\server.py

echo.
echo Le serveur s'est arrete.
pause
