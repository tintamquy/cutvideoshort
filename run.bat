@echo off
REM Phần Mềm Cắt Video Short - PhatDaPhoTe.com
REM Script khởi động cho Windows

echo ======================================================================
echo    PHẦN MỀM CẮT VIDEO SHORT - PhatDaPhoTe.com
echo ======================================================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Khong tim thay Python! Vui long cai dat Python 3.
    pause
    exit /b 1
)

echo [INFO] Dang khoi dong Video Cutter...
echo.

python scripts\video_cutter.py

echo.
echo ======================================================================
echo [FINISH] Hoan thanh tat ca.
pause
