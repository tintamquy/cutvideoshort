@echo off
chcp 65001 >nul
title Phần Mềm Cắt Video Short - PhatDaPhoTe.com
cls

echo ============================================================
echo    PHẦN MỀM CẮT VIDEO SHORT - PhatDaPhoTe.com
echo ============================================================
echo.

REM Kiểm tra Python có được cài đặt không
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt!
    echo 📥 Vui lòng cài đặt Python từ https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Chạy script Python
set PYTHONIOENCODING=utf-8
python video_cutter.py

REM Giữ cửa sổ mở nếu có lỗi
if errorlevel 1 (
    echo.
    echo ❌ Có lỗi xảy ra!
    pause
)
