@echo off
echo 🩺 Starting Medical AI Backend Server...
echo.

REM Activate Python virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Python virtual environment activated
) else (
    echo ⚠️ Python virtual environment not found. Run setup.bat first.
)

REM Check if backend/.env exists
if not exist "backend\.env" (
    echo ⚠️ backend\.env file not found!
    echo Creating from template...
    copy "backend\.env.example" "backend\.env"
    echo ⚠️ Please edit backend\.env and add your GROQ_API_KEY
    echo Then restart this script.
    pause
    exit /b 1
)

REM Start backend server
echo 🚀 Starting backend server on port 3001...
cd backend
npm start

REM If npm start fails, try with node directly
if %errorlevel% neq 0 (
    echo ⚠️ npm start failed, trying with node directly...
    node server.js
)

cd ..
echo.
echo 🛑 Backend server stopped.
pause