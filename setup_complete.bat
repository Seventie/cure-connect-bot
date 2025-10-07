@echo off
echo ===============================================
echo 🩺 MEDICAL AI WEB APP - COMPLETE SETUP
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

:: Create Python virtual environment
echo 📦 Setting up Python virtual environment...
if not exist ".venv" (
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

:: Upgrade pip
echo 📥 Upgrading pip...
python -m pip install --upgrade pip

:: Install Python dependencies
echo 📥 Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️  Some Python packages may have failed to install
    echo This is normal - the app will work with available packages
)

:: Install frontend dependencies
echo 📥 Installing frontend dependencies...
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

:: Install backend dependencies
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

:: Create environment file from template
echo ⚙️  Setting up environment configuration...
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env"
        echo ✅ Created backend/.env from template
        echo ⚠️  IMPORTANT: Edit backend/.env and add your GROQ_API_KEY
    ) else (
        echo # Backend Environment Configuration > "backend\.env"
        echo PORT=3001 >> "backend\.env"
        echo NODE_ENV=development >> "backend\.env"
        echo CORS_ORIGIN=http://localhost:5173 >> "backend\.env"
        echo GROQ_API_KEY=your-groq-api-key-here >> "backend\.env"
        echo ✅ Created basic backend/.env file
    )
) else (
    echo ℹ️  backend/.env already exists
)

:: Check data files
echo 📊 Checking data files...
if exist "data\medquad_processed.csv" (
    echo ✅ MedQuAD data file found
) else (
    echo ⚠️  MedQuAD data file not found (will use fallback)
)

if exist "data\drugs_side_effects.csv" (
    echo ✅ Drugs data file found
) else (
    echo ⚠️  Drugs data file not found (will use fallback)
)

:: Check for embeddings
if exist "embeddings\encoded_docs.npy" (
    echo ✅ Embeddings file found
) else (
    echo ℹ️  Embeddings file not found (will create dummy embeddings)
)

:: Test Python model
echo 🧪 Testing Python QA model...
python models\qa.py --question "What is fever?" --api
if %errorlevel% equ 0 (
    echo ✅ QA model is working
) else (
    echo ⚠️  QA model test failed (will use fallback mode)
)

echo.
echo ===============================================
echo ✅ SETUP COMPLETE!
echo ===============================================
echo.
echo 🚀 To start the application:
echo.
echo 1. Start Backend:
echo    cd backend && npm start
echo.
echo 2. Start Frontend (new terminal):
echo    npm run dev
echo.
echo 3. Open browser:
echo    http://localhost:5173
echo.
echo 💡 Important Notes:
echo - Add your GROQ_API_KEY to backend/.env
echo - Both servers must be running simultaneously
echo - Frontend: http://localhost:5173
echo - Backend API: http://localhost:3001
echo.
echo 🔗 For issues, check: https://github.com/Seventie/cure-connect-bot
echo.
pause