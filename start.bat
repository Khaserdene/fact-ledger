@echo off
title Fact Ledger Platform
color 07

echo.
echo  =============================================================
echo   FACT LEDGER  ^|  System Orchestrator
echo  =============================================================
echo.

set "ROOT_DIR=%~dp0"
set "PYTHON=%ROOT_DIR%backend\venv\Scripts\python.exe"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: Step 1: Database backup
echo  [1/4] Creating database backup snapshot...
cd /d "%BACKEND_DIR%"
if exist "%PYTHON%" (
    "%PYTHON%" scripts\backup_db.py >nul 2>&1
    echo        Database snapshot complete.
) else (
    echo        Notice: Virtual environment python not detected. Skipping local backup.
)

:: Step 2: Database migrations
echo  [2/4] Verifying schema migrations (Alembic)...
if exist "%PYTHON%" (
    "%PYTHON%" -m alembic upgrade head >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  [ERROR] Database migration failed.
        echo  Check backend\alembic.ini or database logs.
        echo.
        pause
        exit /b 1
    )
)
echo        Schema up to date.

:: Step 3: Launch FastAPI backend
echo  [3/4] Initializing backend services (FastAPI on port 8020)...
start "Fact Ledger Backend (:8020)" /MIN cmd /c "cd /d "%BACKEND_DIR%" && "%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8020 --reload"

timeout /t 3 /nobreak >nul

:: Step 4: Launch React frontend
echo  [4/4] Starting frontend client (Vite on port 5200)...
start "Fact Ledger Frontend (:5200)" /MIN cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"

timeout /t 4 /nobreak >nul

echo.
echo  =============================================================
echo   Status: Services online and operational
echo.
echo   Client Application:  http://localhost:5200
echo   API Documentation:   http://localhost:8020/docs
echo.
echo   Press any key or close this terminal to dismiss.
echo  =============================================================
echo.

:: Open default browser
start "" "http://localhost:5200"

pause >nul
