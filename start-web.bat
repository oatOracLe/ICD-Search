@echo off
chcp 65001 >nul
cd /d "%~dp0web"
echo Opening http://localhost:8000  (close this window to stop)
start "" http://localhost:8000/index.html
python -m http.server 8000 || py -m http.server 8000
pause
