@echo off
echo ========================================
echo   ICICI ALGO TRADING - MAIN LAUNCHER
echo ========================================
echo.
echo Choose your system:
echo.
echo 1. Trading System (Real Trading Bot)
echo 2. Khusi Investment Model
echo 3. Exit
echo.
echo ========================================

choice /c 123 /n /m "Enter your choice (1-3): "

if errorlevel 3 goto :end
if errorlevel 2 goto :khusi
if errorlevel 1 goto :trading

:trading
echo.
echo Starting Trading System...
echo ========================================
cd "Trading_System"
call START_TRADING_SYSTEM.bat
goto :end

:khusi
echo.
echo Starting Khusi Investment Model...
echo ========================================
cd "Khusi_Investment_Model"
C:\Users\abhis\Anaconda3\Scripts\conda.exe run -p "..\..\.conda" --no-capture-output python Khusi_Invest_Model.py
pause
goto :end

:end
echo.
echo Goodbye!
