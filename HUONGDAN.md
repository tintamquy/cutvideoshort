# Hướng Dẫn Sử Dụng Phần Mềm Cắt Video Short

## 📋 Yêu Cầu

### Windows
- ✅ Python 3.x (nếu chưa có, tải tại python.org)
- ✅ FFmpeg (đã có sẵn trong folder)

### macOS
- ✅ Python 3 (thường đã có sẵn)
- ✅ FFmpeg (cài qua Homebrew: `brew install ffmpeg`)

## 🚀 Cách Sử Dụng

### 1. Chuẩn Bị Input

Đặt video và subtitle vào folder `input/`:
- Video: `tenvideo.mp4` (hoặc .avi, .mov, .mkv)
- Subtitle: `tenvideo.srt` (cùng tên với video)
- **Nhạc nền** (optional): Đặt file `nhacnen.mp3` trong folder chính

### 2. Cấu Hình (config.json)

```json
{
  "min_segment_duration": 50,      // Độ dài tối thiểu (giây)
  "max_segment_duration": 170,     // Độ dài tối đa (2p50s)
  "min_pause_duration": 4.0,       // Khoảng im lặng để cắt
  "zoom_factor": 1.15,             // Zoom 15%
  "background_music": {
    "enabled": true,               // Bật/tắt nhạc nền
    "file": "nhacnen.mp3",        // Tên file nhạc
    "volume": 0.10                // Âm lượng (10%)
  },
  "groq_ai": {
    "enabled": false,              // Bật AI phân tích (optional)
    "api_key": ""                  // API key Groq (miễn phí)
  }
}
```

### 3. Chạy Phần Mềm

#### Windows
Double-click vào file **`run.bat`**

#### macOS/Linux
```bash
chmod +x run.sh    # Lần đầu tiên cần cấp quyền
./run.sh           # Chạy
```

### 4. Lấy Kết Quả

Video đã cắt sẽ nằm trong folder:
```
output/
  └── tenvideo/
      ├── 01_chu_de_dau_tien.mp4
      ├── 02_chu_de_thu_hai.mp4
      └── ...
```

## 🎵 Nhạc Nền

- File nhạc nền: **`nhacnen.mp3`** (đặt cùng folder với run.bat/run.sh)
- Âm lượng: **10%** (có thể điều chỉnh trong config.json: 0.05-0.20)
- Nhạc sẽ **loop tự động** nếu video dài hơn nhạc

## 🍎 Cài Đặt Trên macOS

### Cài FFmpeg (bắt buộc)
```bash
# Cài Homebrew (nếu chưa có)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Cài FFmpeg
brew install ffmpeg
```

### Cài Python (nếu cần)
```bash
brew install python3
```

### Chạy Phần Mềm
```bash
cd /path/to/Cut-Short-Video
chmod +x run.sh
./run.sh
```

## 🤖 Tích Hợp AI (Optional - Miễn Phí)

Để AI phân tích semantic và cắt chính xác hơn:

### Cách Lấy API Key Groq Miễn Phí:

1. Truy cập: https://console.groq.com
2. Sign up (miễn phí, không cần thẻ tín dụng)
3. Vào **API Keys** → **Create API Key**
4. Copy API key
5. Paste vào `config.json`:
   ```json
   "groq_ai": {
     "enabled": true,
     "api_key": "gsk_xxxxxxxxxxxxx"
   }
   ```

**Lợi ích**:
- ✅ Phân tích ý nghĩa semantic
- ✅ Cắt đoạn chính xác hơn (câu đầu/cuối hoàn chỉnh)
- ✅ Hoàn toàn miễn phí (30 requests/phút)

## ⚙️ Tùy Chỉnh

### Thay Đổi Độ Dài Video
Sửa trong `config.json`:
```json
"min_segment_duration": 50,   // Tối thiểu (50s)
"max_segment_duration": 170,  // Tối đa (2p50s)
```

### Thay Đổi Âm Lượng Nhạc Nền
```json
"volume": 0.10  // 0.05 = 5%, 0.10 = 10%, 0.20 = 20%
```

### Tắt Nhạc Nền
```json
"background_music": {
  "enabled": false
}
```

## 📊 Kết Quả

Mỗi video sẽ có:
- ✅ Độ dài: 50s - 2p50s
- ✅ Tỷ lệ: 9:16 (vertical)
- ✅ Watermark: "PhatDaPhoTe.com"
- ✅ Logo overlay
- ✅ Nhạc nền (10% volume)
- ✅ Câu đầu/cuối hoàn chỉnh
- ✅ Tên file có ý nghĩa

## ❓ Gặp Lỗi?

### Windows
**Lỗi: "Không tìm thấy ffmpeg.exe"**
→ Đảm bảo file `ffmpeg.exe` nằm cùng folder với `run.bat`

### macOS
**Lỗi: "command not found: ffmpeg"**
→ Cài FFmpeg: `brew install ffmpeg`

**Lỗi: "Permission denied"**
→ Cấp quyền: `chmod +x run.sh`

### Chung
**Lỗi: "Không tìm thấy nhacnen.mp3"**
→ Đặt file nhạc trong folder chính, hoặc tắt nhạc nền trong config

**Video không có nhạc nền**
→ Kiểm tra `background_music.enabled = true` trong config.json

## 🔧 Nâng Cao

### Python Dependencies (nếu cần)
```bash
pip install requests  # Chỉ cần nếu dùng Groq AI
```

### FFmpeg Custom Path
Nếu FFmpeg ở vị trí khác, sửa trong `video_cutter.py`:
```python
self.ffmpeg_path = '/usr/local/bin/ffmpeg'  # macOS
self.ffmpeg_path = 'C:\\ffmpeg\\bin\\ffmpeg.exe'  # Windows
```

## 📞 Liên Hệ

Website: PhatDaPhoTe.com
