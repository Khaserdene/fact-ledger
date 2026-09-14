@echo off
title FACT LEDGER — Платформ
color 0A

echo.
echo  ================================================
echo   FACT LEDGER платформ асаж байна...
echo  ================================================
echo.

set PYTHON=%~dp0backend\venv\Scripts\python.exe
set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend

:: Өгөгдлийн сангийн нөөц
echo  [1/4] Өгөгдлийн санг нөөцөлж байна...
cd /d %BACKEND_DIR%
"%PYTHON%" scripts\backup_db.py

:: Схемийн шинэчлэл (Alembic)
echo  [2/4] Схемийн шинэчлэл шалгаж байна...
"%PYTHON%" -m alembic upgrade head
if errorlevel 1 (
    echo.
    echo  АЛДАА: Migration амжилтгүй! backups\ хавтаснаас сэргээх боломжтой.
    pause
    exit /b 1
)

:: Backend асаах
echo  [3/4] Backend (FastAPI) асаж байна...
start "Backend — FastAPI :8020" /MIN cmd /c "cd /d %BACKEND_DIR% && "%PYTHON%" -m uvicorn main:app --host 127.0.0.1 --port 8020 --reload"

:: Бага зэрэг хүлээх
timeout /t 3 /nobreak >nul

:: Frontend асаах
echo  [4/4] Frontend (React) асаж байна...
start "Frontend — React :5200" /MIN cmd /c "cd /d %FRONTEND_DIR% && npm run dev"

:: Хүлээх
timeout /t 6 /nobreak >nul

echo.
echo  ================================================
echo   Амжилттай!
echo.
echo   Платформ: http://localhost:5200
echo   API:      http://localhost:8020
echo.
echo   Хаахын тулд энэ цонхыг хаана уу.
echo  ================================================
echo.

:: Браузерт нээх
start "" "http://localhost:5200"

pause
