@echo off
chcp 65001 > nul
setlocal

echo ========================================
echo  Patcher Web - Jack Bros (Virtual Boy) FR
echo ========================================
echo.
echo Le navigateur va s'ouvrir sur http://localhost:8080
echo Appuyez sur Ctrl+C dans cette fenetre pour arreter.
echo.

cd /d "%~dp0"

REM Le navigateur etait ouvert AVANT le demarrage du serveur, ce qui donnait
REM un "connexion refusee" au premier chargement. On attend deux secondes,
REM en tache de fond, pendant que le serveur demarre juste apres.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command ^
  "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8080'"

python -m http.server 8080
if errorlevel 1 (
    echo.
    echo Python introuvable, tentative avec npx...
    npx serve . -p 8080
)
