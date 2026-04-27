@echo off
title YouTube Automation Engine — Setup
color 0B

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║  🚀 YOUTUBE AUTOMATION ENGINE — GOD MODE SETUP              ║
echo ║  Cost: ₹0 ^| Stack: Gemini + Edge TTS + Pollinations + FFmpeg ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Download from https://python.org
    pause & exit
)
python --version
echo ✅ Python found

:: Check FFmpeg
echo.
echo [2/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg not found. Installing via winget...
    winget install ffmpeg -e --silent
    if errorlevel 1 (
        echo ❌ Auto-install failed. Download from https://ffmpeg.org/download.html
        echo    Press any key after manual install...
        pause >nul
    )
) else (
    echo ✅ FFmpeg found
)

:: Check Node.js
echo.
echo [3/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Download from https://nodejs.org
    pause & exit
)
node --version
echo ✅ Node.js found

:: Create folders
echo.
echo [4/6] Creating folders...
if not exist output\scripts mkdir output\scripts
if not exist output\audio mkdir output\audio
if not exist output\images mkdir output\images
if not exist output\videos mkdir output\videos
if not exist output\thumbnails mkdir output\thumbnails
if not exist output\logs mkdir output\logs
if not exist temp mkdir temp
if not exist templates\music mkdir templates\music
echo ✅ Folders created

:: Install Python dependencies
echo.
echo [5/6] Installing Python packages (edge-tts, requests, Pillow)...
pip install -r requirements.txt -q
echo ✅ Python packages installed

:: Setup .env
echo.
echo [6/6] Setting up .env...
if not exist .env (
    copy .env.example .env >nul
    echo ✅ .env created from template
    echo.
    echo ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    echo  ACTION REQUIRED:
    echo  Open .env and add your GEMINI_API_KEY
    echo  Get FREE key: https://aistudio.google.com/apikey
    echo ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
) else (
    echo ✅ .env already exists
)

:: Install dashboard dependencies
echo.
echo Installing dashboard (Express.js)...
cd dashboard
call npm install --silent
cd ..
echo ✅ Dashboard ready

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║  ✅ SETUP COMPLETE!                                          ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  NEXT STEPS:                                                 ║
echo ║  1. Edit .env → add GEMINI_API_KEY                          ║
echo ║  2. Run: start.bat                                           ║
echo ║  3. Open: http://localhost:3000                              ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
pause
