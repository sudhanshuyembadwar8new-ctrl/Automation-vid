@echo off
title YouTube Automation — GOD MODE
color 0B

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║  🚀 Starting YouTube Automation Engine...        ║
echo ╚═══════════════════════════════════════════════════╝
echo.

:: Start dashboard in background
echo 🌐 Starting dashboard at http://localhost:3000...
cd dashboard
start /B cmd /c "npm start 2>&1"
cd ..
timeout /t 2 /nobreak >nul

:: Open browser
start http://localhost:3000

echo ✅ Dashboard running at http://localhost:3000
echo.
echo ─────────────────────────────────────────────────────
echo  Quick commands (run in another terminal):
echo.
echo  Generate short:  python pipeline.py --type short --dry-run
echo  Generate long:   python pipeline.py --type long --dry-run
echo  Custom topic:    python pipeline.py --topic "your topic here" --dry-run
echo  Batch 7 shorts:  python pipeline.py --batch 7 --type short --dry-run
echo  Test voice:      python scripts/generate_voice.py --text "Bhai sun, ye free hai"
echo ─────────────────────────────────────────────────────
echo.
echo Press Ctrl+C to stop dashboard
echo.
cd dashboard
node server.js
