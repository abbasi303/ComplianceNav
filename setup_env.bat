@echo off
echo 🏛️ ========================================
echo    ComplianceNavigator Environment Setup
echo    Windows Batch Script
echo 🏛️ ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

REM Check Python version (basic check)
echo.
echo 📦 Setting up virtual environment...

REM Remove existing venv if it exists
if exist venv (
    echo    Removing existing virtual environment...
    rmdir /s /q venv
)

REM Create virtual environment
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created

REM Activate virtual environment
echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo 📦 Installing project dependencies...
echo    This may take a few minutes...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    echo    Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ✅ All dependencies installed successfully!

REM Set up environment file
echo.
echo ⚙️ Setting up environment configuration...
if not exist .env (
    if exist .env_template (
        copy .env_template .env >nul
        echo ✅ Environment file (.env) created from template
    ) else (
        echo ⚠️ .env_template not found, you'll need to create .env manually
    )
) else (
    echo ✅ Environment file (.env) already exists
)

REM Create necessary directories
echo.
echo 📁 Creating project directories...
if not exist data mkdir data
if not exist data\chroma_db mkdir data\chroma_db
if not exist data\regulations mkdir data\regulations
if not exist logs mkdir logs
echo ✅ Directories created

REM Display next steps
echo.
echo 🎉 Setup Complete!
echo.
echo 📝 Next Steps:
echo    1. Edit .env file and add your GEMINI_API_KEY
echo    2. To run the application:
echo       - Activate environment: venv\Scripts\activate.bat
echo       - Start web app: python main.py
echo       - Or use CLI: python main.py cli
echo.
echo 🔑 Get your Gemini API key at:
echo    https://makersuite.google.com/app/apikey
echo.

pause 