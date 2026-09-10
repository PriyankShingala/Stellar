@echo off
echo ===================================================
echo   Stellar-AI / PRAYOG-AI Windows Setup Script
echo ===================================================
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo Setup complete! Run deployment\run_app.bat to launch application.
pause
