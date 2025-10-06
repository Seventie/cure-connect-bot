@echo off
echo 🌐 Starting Medical AI Frontend...
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo ⚠️ Frontend dependencies not installed!
    echo Installing dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start frontend development server
echo 🚀 Starting frontend development server...
echo 🔗 Frontend will be available at: http://localhost:5173
echo 🔗 Backend API should be running at: http://localhost:3001
echo.
echo 📄 Make sure the backend is running in another terminal!
echo.

call npm run dev

REM If npm run dev fails, show helpful message
if %errorlevel% neq 0 (
    echo.
    echo ❌ Frontend server failed to start
    echo 📄 Try these steps:
    echo   1. Make sure Node.js 16+ is installed
    echo   2. Delete node_modules and run: npm install
    echo   3. Check if port 5173 is already in use
    echo.
)

echo.
echo 🛑 Frontend server stopped.
pause