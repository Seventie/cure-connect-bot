@echo off
echo 🩺 Setting up Medical AI Web Application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Python and Node.js found
echo.



REM Install Python dependencies
echo 🔄 Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Install Node.js dependencies
echo 🔄 Installing frontend dependencies...
call npm install

echo 🔄 Installing backend dependencies...
cd backend
call npm install
cd ..

REM Create environment files
echo 🔄 Creating environment configuration...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo ⚠️ Please edit backend\.env and add your GROQ_API_KEY
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 To start the application:
echo    1. Open TWO command prompts in this folder
echo    2. In first prompt: run_backend.bat
echo    3. In second prompt: run_frontend.bat
echo    4. Open browser to http://localhost:5173
echo.
pause