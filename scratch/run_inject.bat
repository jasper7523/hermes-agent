@echo off
title Antigravity IDE Convo Injector
echo ============================================================
echo  Antigravity IDE Convo Injector (Session #146 Recovery)
echo ============================================================
echo.
echo [1/2] Force-closing any running/stuck Antigravity IDE background processes...
powershell -Command "Stop-Process -Name '*Antigravity*' -Force -ErrorAction SilentlyContinue"
echo.
echo [2/2] Running injector script...
python d:\hermes-agent\scratch\inject_conversation.py
echo.
echo ============================================================
echo Process finished. You can now restart Antigravity IDE.
echo ============================================================
pause
