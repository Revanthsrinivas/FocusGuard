@echo off
echo ============================================
echo     FOCUSGUARD OVERNIGHT DATA COLLECTION
echo ============================================
echo.
echo This script will:
echo 1. Open YouTube with varied content
echo 2. Start FocusGuard data collection
echo 3. Run for 24 hours (or until you stop)
echo 4. Save all collected data
echo.
echo DO NOT CLOSE THIS WINDOW!
echo.
pause

cd /d "C:\Users\abhij\Downloads\FocusGuard\FocusGuard"

REM Open YouTube in background
start python scripts\youtube_autoplay.py

REM Wait for YouTube to load
timeout /t 10 /nobreak

REM Start overnight collection (24h default)
python scripts\overnight_collector.py --duration 24

echo.
echo Collection complete! Check data/training_data.json
pause
