# 🎬 Phần Mềm Cắt Video Short - PhatDaPhoTe.com

Công cụ tự động cắt video dài thành các đoạn short có ý nghĩa (50s-2p50s), chuyển 16:9 → 9:16, thêm watermark, logo, và nhạc nền.

## ✨ Tính Năng

- 🎯 **Tự động cắt đoạn**: Phân tích subtitle để tìm đoạn có ý nghĩa trọn vẹn
- ⏱️ **Độ dài linh hoạt**: 50 giây - 2 phút 50 giây
- 📱 **9:16 vertical**: Chuyển từ 16:9 sang format short video
- 🎨 **Blur background**: Làm mờ phần trống 2 bên
- 🏷️ **Watermark**: Thêm watermark "PhatDaPhoTe.com"
- 🖼️ **Logo overlay**: Phủ logo của bạn lên video
- 🎵 **Nhạc nền**: Tự động mix nhạc nền (10% volume)
- 🤖 **AI phân tích**: Tích hợp Groq AI (optional, miễn phí)
- 💻 **Cross-platform**: Windows, macOS, Linux

## 📋 Yêu Cầu

### Windows
- Python 3.7+
- FFmpeg ([Download](https://ffmpeg.org/download.html))

### macOS
- Python 3 (đã có sẵn)
- FFmpeg: `brew install ffmpeg`

### Linux
- Python 3: `sudo apt install python3`
- FFmpeg: `sudo apt install ffmpeg`

## 🚀 Cài Đặt

### 1. Clone Repository
```bash
git clone https://github.com/tintamquy/cutvideoshort.git
cd cutvideoshort
```

### 2. Download FFmpeg (Windows)
- Tải FFmpeg: https://ffmpeg.org/download.html
- Giải nén và copy `ffmpeg.exe` vào folder dự án

### 3. Chuẩn Bị Assets
- Tạo logo 9:16: Lưu thành `9-16logo.png` (optional)
- Chuẩn bị nhạc nền: Lưu thành `nhacnen.mp3` (optional)

## 📖 Hướng Dẫn Sử Dụng

### 1. Chuẩn Bị Input
Đặt video và subtitle vào folder `input/`:
```
input/
├── video.mp4
└── video.srt
```

### 2. Chạy Phần Mềm

#### Windows
```bash
run.bat
```

#### macOS/Linux
```bash
chmod +x run.sh
./run.sh
```

### 3. Lấy Kết Quả
Video đã cắt sẽ nằm trong `output/video/`:
```
output/
└── video/
    ├── 01_chu_de_dau_tien.mp4
    ├── 02_chu_de_thu_hai.mp4
    └── ...
```

## ⚙️ Cấu Hình

Chỉnh sửa `config.json`:

```json
{
  "min_segment_duration": 50,
  "max_segment_duration": 170,
  "min_pause_duration": 4.0,
  "zoom_factor": 1.15,
  "background_music": {
    "enabled": true,
    "file": "nhacnen.mp3",
    "volume": 0.10
  },
  "groq_ai": {
    "enabled": false,
    "api_key": ""
  }
}
```

## 🤖 AI Phân Tích (Optional)

1. Đăng ký Groq (miễn phí): https://console.groq.com
2. Lấy API key
3. Cập nhật `config.json`:
```json
"groq_ai": {
  "enabled": true,
  "api_key": "gsk_your_api_key_here"
}
```

## 📞 Liên Hệ

- Website: PhatDaPhoTe.com
- GitHub: https://github.com/tintamquy/cutvideoshort

**Made with ❤️ by PhatDaPhoTe.com**
