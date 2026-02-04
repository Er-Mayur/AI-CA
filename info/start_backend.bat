@echo off
echo Starting AI-CA Backend Server...
echo.

cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt -q

if not exist aica.db (
    echo Initializing database...
    python seed_tax_rules.py
)

echo.
echo ========================================
echo AI-CA Backend Server Starting...
echo API Documentation: http://localhost:8000/docs
echo ========================================
echo.

python main.py

pause

