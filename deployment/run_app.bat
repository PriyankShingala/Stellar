@echo off
echo Starting Stellar-AI Desktop Application...
cd /d "%~dp0\.."
call venv\Scripts\activate
python -m frontend.app
pause
