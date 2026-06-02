@echo off
chcp 65001 >nul
echo ============================================================
echo   Antigravity IDE - Ultimate Sidebar History Recovery
echo   (Keeps both old history and all available recent history)
echo ============================================================
echo.
echo [1/4] Closing Antigravity IDE...
taskkill /IM "Antigravity IDE.exe" /F >nul 2>&1
echo      Waiting 5 seconds for database flush...
timeout /t 5 /nobreak >nul

echo.
echo [2/4] Running Ultimate Recovery Script...
python d:\hermes-agent\scratch\recover_all_history.py
echo.

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Recovery failed! Please check the output above.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [3/4] Restarting Antigravity IDE...
start "" "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"

echo.
echo [4/4] DONE!
echo   All possible conversation histories from backups and
echo   individual .pb files have been successfully merged.
echo.
echo   Check your "Past Conversations" sidebar in the IDE.
echo ============================================================
pause >nul
