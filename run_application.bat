@echo off
echo ===============================================
echo 🩺 MEDICAL AI WEB APPLICATION RUNNER
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Python and Node.js detected
echo.

:: Create Python virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ℹ️  Virtual environment already exists
)

:: Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install Python dependencies if needed
echo 📥 Ensuring Python dependencies are installed...
pip install -q flask flask-cors requests pandas numpy scikit-learn faiss-cpu
if %errorlevel% neq 0 (
    echo ⚠️  Some Python packages may have failed to install
    echo This is normal - the app will work with available packages
)

:: Check for Node dependencies
if not exist "node_modules" (
    echo 📥 Installing frontend dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

if not exist "backend\node_modules" (
    echo 📥 Installing backend dependencies...
    cd backend
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install backend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

echo.
echo 🚀 Starting Medical AI Application...
echo This will start all services in the correct order
echo Please wait for all models to load completely
echo.

:: Run the comprehensive application runner
python run_application.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Application failed to start
    echo Check application.log for detailed error information
    echo.
    echo 🔧 Troubleshooting steps:
    echo 1. Ensure all required data files are present
    echo 2. Check that no other services are using ports 3001, 5001, 5002, 5003, 5173
    echo 3. Try running individual components manually
    echo 4. Check the GitHub repository README for setup instructions
    pause
    exit /b 1
)

echo.
echo ✅ Application has been shut down successfully
pause