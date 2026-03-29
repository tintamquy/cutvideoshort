#!/bin/bash
# Phần Mềm Cắt Video Short - PhatDaPhoTe.com
# Script cho macOS/Linux

clear

echo "======================================================================"
echo "   PHẦN MỀM CẮT VIDEO SHORT - PhatDaPhoTe.com"
echo "======================================================================"
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 chưa được cài đặt!"
    echo "Vui lòng cài đặt Python 3 từ: https://www.python.org/downloads/"
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

# Kiểm tra ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  Không tìm thấy ffmpeg!"
    echo ""
    echo "Hướng dẫn cài đặt FFmpeg trên macOS:"
    echo "1. Cài Homebrew (nếu chưa có):"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "2. Cài FFmpeg:"
    echo "   brew install ffmpeg"
    echo ""
    read -p "Nhấn Enter để thoát..."
    exit 1
fi

# Chạy script Python
echo "🚀 Đang khởi động..."
echo ""

python3 scripts/video_cutter.py

echo ""
read -p "Nhấn Enter để thoát..."
