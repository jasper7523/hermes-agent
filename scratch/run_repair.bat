@echo off
chcp 65001 >nul
echo ============================================================
echo   Antigravity IDE Sidebar Index Repair
echo   This window will stay open independently of the IDE.
echo ============================================================
echo.

echo [Step 1] Waiting 5 seconds for you to switch to this window...
timeout /t 5 /nobreak

echo.
echo [Step 2] Closing Antigravity IDE...
taskkill /IM "Antigravity IDE.exe" /F >nul 2>&1
echo   Waiting 8 seconds for state.vscdb to flush to disk...
timeout /t 8 /nobreak

echo.
echo [Step 3] Running repair script...
python "d:\hermes-agent\scratch\repair_sidebar_index.py"

echo.
echo [Step 4] Restarting Antigravity IDE...
start "" "%LOCALAPPDATA%\Programs\Antigravity IDE\Antigravity IDE.exe"

echo.
echo ============================================================
echo   DONE! IDE is restarting.
echo   Check Past Conversations in the sidebar.
echo   You can close this window now.
echo ============================================================
pause
