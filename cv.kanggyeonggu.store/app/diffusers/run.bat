@echo off
REM Diffusion 서버 실행 스크립트 (Windows)
cd /d "%~dp0\..\.."
uvicorn app.diffusers.main:app --host 0.0.0.0 --port 8000 --reload

