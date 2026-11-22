@echo off
cd /d %~dp0
set PY=python
where python >nul 2>nul || set PY=py
echo Installing ResQLink backend requirements...
%PY% -m pip install -r backend\requirements.txt
if errorlevel 1 (echo. & echo Python not found or install failed. Install Python 3.10+ from python.org, tick "Add to PATH", then run again. & echo Backup: open standalone\ResQLink.html & pause & exit /b)
echo.
echo Starting ResQLink on http://localhost:8000  (phones: scan the QR code on the command centre)
start "" http://localhost:8000
%PY% -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
pause
