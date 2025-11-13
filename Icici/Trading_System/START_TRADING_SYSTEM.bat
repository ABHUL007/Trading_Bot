@echo off
echo ========================================
echo   UNIFIED TRADING SYSTEM LAUNCHER
echo ========================================
echo.
echo Starting both:
echo   1. Websocket Data Collector
echo   2. Real Trader Bot
echo.
echo Press Ctrl+C to stop both systems
echo ========================================
echo.

cd /d "d:\Algo Trading\Icici\Trading_System"
C:\Users\abhis\Anaconda3\Scripts\conda.exe run -p "d:\Algo Trading\Icici\.conda" --no-capture-output python start_trading_system.py

pause
