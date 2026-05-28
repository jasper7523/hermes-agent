@echo off
chcp 65001 >nul
echo ======================================================
echo   Antigravity IDE Sidebar MERGE Repair v2
echo ======================================================
echo.
echo [1/4] Waiting 5 seconds before closing IDE...
timeout /t 5 /nobreak >nul

echo [2/4] Closing Antigravity IDE...
taskkill /IM "Antigravity IDE.exe" /F >nul 2>&1
echo      Waiting 8 seconds for database flush...
timeout /t 8 /nobreak >nul

echo [3/4] Running MERGE repair script...
python d:\hermes-agent\scratch\repair_v2_merge.py
echo.

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Repair failed! Restoring backup...
    copy /Y "%APPDATA%\Antigravity IDE\User\globalStorage\state.vscdb.pre_sidebar_fix_20260528_144054" "%APPDATA%\Antigravity IDE\User\globalStorage\state.vscdb" >nul
    echo [OK] Backup restored.
)

echo [4/4] Restarting Antigravity IDE...
start "" "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"

echo.
echo Done! Check Past Conversations in sidebar.
echo Press any key to close this window...
pause >nul
