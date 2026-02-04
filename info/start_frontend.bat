@echo off
echo Starting AI-CA Frontend Server...
echo.

cd frontend

if not exist node_modules (
    echo Installing dependencies...
    npm install
)

echo.
echo ========================================
echo AI-CA Frontend Starting...
echo Application: http://localhost:3000
echo ========================================
echo.

npm run dev

pause

