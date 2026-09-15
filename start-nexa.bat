@echo off
echo Starting Nexa AI...

REM Backend ko ek NAYI window mein start karo
start "Nexa AI - Backend" cmd /k "cd /d D:\nexa-ai\backend && D:\nexa-ai\.venv\Scripts\activate.bat && uvicorn main:app --reload"

REM 3 second wait karo taaki backend pehle start ho jaye
timeout /t 3 /nobreak > nul

REM Frontend + Electron ko ek ALAG NAYI window mein start karo
start "Nexa AI - Frontend" cmd /k "cd /d D:\nexa-ai\frontend && npm run electron:dev"

echo Nexa AI is starting in separate windows...
