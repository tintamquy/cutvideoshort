#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Cutter - Cắt video dài thành các đoạn short có ý nghĩa
Chuyển đổi video 16:9 sang 9:16 với blur background, title, watermark và logo
"""

import os
import re
import json
import subprocess
import sys
import io
import shutil
from datetime import timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ép hệ thống dùng UTF-8 trên Windows để in được emoji (Ngăn lỗi UnicodeEncodeError khi print)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class SubtitleSegment:
    """Đại diện cho một đoạn subtitle"""
    def __init__(self, index: int, start_time: float, end_time: float, text: str):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.duration = end_time - start_time


class SubtitleParser:
    """Parse file .srt thành danh sách segments"""
    
    @staticmethod
    def parse_srt(srt_path: str) -> List[SubtitleSegment]:
        """Parse file SRT và trả về danh sách SubtitleSegment"""
        segments = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Thử encoding khác nếu utf-8 fail
            with open(srt_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        
        # Tách các subtitle blocks
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            try:
                # Line 1: Index
                index = int(lines[0].strip())
                
                # Line 2: Timestamps
                time_line = lines[1].strip()
                start_str, end_str = time_line.split(' --> ')
                start_time = SubtitleParser._parse_timestamp(start_str)
                end_time = SubtitleParser._parse_timestamp(end_str)
                
                # Line 3+: Text
                text = ' '.join(lines[2:]).strip()
                
                segments.append(SubtitleSegment(index, start_time, end_time, text))
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Lỗi parse subtitle block: {e}")
                continue
        
        return segments
    
    @staticmethod
    def _parse_timestamp(timestamp: str) -> float:
        """Chuyển đổi timestamp SRT (HH:MM:SS,mmm) sang giây"""
        # Format: 00:00:00,766 hoặc 00:00:00.766
        timestamp = timestamp.replace(',', '.')
        parts = timestamp.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds


class OpenClawAI:
    """Tích hợp OpenClaw API để phân tích semantic và độ viral"""
    
    def __init__(self, api_key: str, model: str = "claude-haiku-4.5", enabled: bool = True):
        self.api_key = api_key
        self.model = model
        self.enabled = enabled and bool(api_key)
        self.base_url = "https://llm.chiasegpu.vn/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_subtitles(self, subtitle_text: str, max_duration: int = 179) -> Optional[List[Dict]]:
        """Gửi SRT lên AI để chọn ra các đoạn video viral"""
        if not self.enabled:
            return None
            
        try:
            import requests
            
            prompt = f"""Bạn là một chuyên gia sáng tạo nội dung viral về Phật pháp, am hiểu cách thu hút người xem một cách trang nghiêm, tinh tế.
Hãy phân tích file phụ đề (subtitle) sau đây và chọn ra những phân đoạn có nội dung hấp dẫn, trọn vẹn ý nghĩa, có khả năng viral cao.

========== QUY TRÌNH BẮT BUỘC CHO MỖI ĐOẠN ==========

BƯỚC 0 — SỬA LỖI CHÍNH TẢ VÀ HIỂU ĐÚNG NGHĨA (QUAN TRỌNG):
   - Phụ đề do máy tạo tự động nên chắc chắn chứa nhiều lỗi chính tả, sai dấu, nhận diện sai thuật ngữ Phật giáo hoặc tên người.
   - BẮT BUỘC bạn phải tự "sửa lỗi" trong đầu để hiểu đúng ngữ nghĩa gốc của câu chuyện TRƯỚC KHI làm các bước tiếp theo.
   - Tiêu đề bạn tạo ra ở Bước 2 TUYỆT ĐỐI KHÔNG ĐƯỢC lặp lại các chữ sai chính tả có trong phụ đề. Phải dùng từ ngữ chuẩn xác, đúng ngữ pháp.
   (Lưu ý: riêng trường `hook_sentence` giữ nguyên văn chữ của phụ đề để tool có thể dò tìm, nhưng `title` phải đúng chính tả 100%).

BƯỚC 1 — CHỌN ĐOẠN NỘI DUNG TRỌN VẸN VÀ TÌM CÂU MỞ ĐẦU HAY:
   - Dựa trên phụ đề, hãy xác định các phần có nội dung mang ý nghĩa trọn vẹn, truyền tải một bài học sâu sắc hoặc câu chuyện giá trị.
   - Trong phần nội dung đó, hãy CHỌN LỌC KỸ CÀNG một câu mở đầu thật sự hay, có ý nghĩa, và chạm đến người nghe. Không cần phải là câu "gây sốc", nhưng phải là câu dẫn dắt mượt mà, sâu sắc và liên quan trực tiếp đến thông điệp cốt lõi.
   - Câu mở đầu đón phải đứng vững được khi là câu đầu tiên của một video. TUYỆT ĐỐI CẤM các câu mào đầu như: "Hôm nay thầy... ", "Như các bạn đã biết...", "Bạch thầy...", "Thưa quý vị...".
   → `start_time` PHẢI trỏ ngay vào chính câu mở đầu tinh túy đó.

BƯỚC 2 — ĐẶT TIÊU ĐỀ DỰA TRÊN CÂU MỞ ĐẦU:
   - Tiêu đề PHẢI được đúc kết từ chính câu mở đầu ở Bước 1. Điều này đảm bảo khi người xem đọc tiêu đề xong, câu đầu tiên họ nghe thấy sẽ là câu trả lời/giải thích liên quan trực tiếp đến tiêu đề đó.
   - Ví dụ câu mở đầu là: "Chúng ta cứ mải mê chạy theo hạnh phúc bên ngoài, mà quên mất sự tĩnh lặng ở bên trong..."
     → Tiêu đề: "Bạn đang tìm hạnh phúc ở đâu?" ✅
   - Ví dụ câu mở đầu: "Tại sao ta tu tập rất lâu mà tâm vẫn không an? Bởi vì ta chưa buông được..."
     → Tiêu đề: "Tu tập lâu mà tâm vẫn không an?" ✅
   - TUYỆT ĐỐI KHÔNG đặt tiêu đề chung chung không liên quan đến câu đầu tiên.
   - ĐỘ DÀI tiêu đề: 4 đến 8 từ, trang nghiêm, không giật tít, không thêm "Clip 1", "Đoạn 2"...

BƯỚC 3 — MỞ RỘNG ĐỦ ĐỘ DÀI (CỰC KỲ QUAN TRỌNG):
   - Tuyệt đối CẤM việc chỉ lấy đúng câu mở đầu rồi kết thúc luôn (tạo ra các đoạn siêu ngắn 3s - 5s). ĐÂY LÀ LỖI RẤT NẶNG.
   - Từ câu mở đầu đó, bạn PHẢI tiếp tục lấy thêm các câu phía sau để tạo thành một đoạn video CÓ TỔNG THỜI LƯỢNG TỐI THIỂU là 50 GIÂY và TỐI ĐA là {max_duration} giây.
   - Luôn nhớ: `end_time` trừ đi `start_time` PHẢI LỚN HƠN HOẶC BẰNG 50. Hãy kiểm tra lại phép toán này trước khi xuất kết quả!
   - Đảm bảo đoạn văn kết thúc ở một câu hoàn chỉnh, tránh cắt cụt.

BƯỚC 4 — CHẤM ĐIỂM ĐÁNH GIÁ (VIRAL SCORE):
   Chấm viral_score từ 1–10. Ưu tiên những đoạn nội dung thật sự giá trị và ý nghĩa, câu đầu tiên đủ độ "chạm". Chỉ giữ những đoạn được 7/10 trở lên.

==========================================================================

QUY TẮC THỜI GIAN:
- Cột mốc trong ngoặc vuông [] tính bằng TỔNG SỐ GIÂY (Ví dụ: [130.50s]).
- Khi trả JSON, BÊ NGUYÊN CON SỐ ĐÓ vào `start_time` và `end_time`. KHÔNG tự quy đổi.

TÌM CÀNG NHIỀU ĐOẠN VIRAL CÀNG TỐT. Với video dài (30 phút - 1 tiếng), BẮT BUỘC phải quét toàn bộ, không bỏ sót phần giữa hay cuối.
CHỈ TRẢ VỀ MỘT MẢNG JSON THUẦN TÚY, KHÔNG BÌNH LUẬN GÌ THÊM.

Subtitles:
{subtitle_text}

Mẫu JSON TRẢ VỀ:
[
  {{
    "start_time": 120.50,
    "end_time": 215.00,
    "hook_sentence": "Câu hook chính xác bạn đã chọn ở Bước 1 (trích nguyên văn từ phụ đề)",
    "title": "Tiêu đề rút ra từ câu hook đó (4-8 từ)",
    "viral_score": 9,
    "reason": "Lý do ngắn gọn: tại sao câu hook này đủ mạnh để mở đầu clip"
  }}
]"""
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4
            }
            
            print(f"  🤖 (AI Model: {self.model}) đang đọc kịch bản và phân tích độ viral (có thể mất 1-2 phút)...")
            response = requests.post(self.base_url, json=data, headers=self.headers, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                import json
                try:
                    return json.loads(content.strip())
                except json.JSONDecodeError:
                    print(f"⚠️ Lỗi Parse JSON. Trả về thực tế: {content}")
                    return None
            else:
                print(f"⚠️ OpenClaw API lỗi: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ OpenClaw API không khả dụng: {e}")
            return None


class VideoSegment:
    """Đại diện cho một đoạn video sẽ được cắt ra"""
    def __init__(self, start_time: float, end_time: float, title: str, subtitle_text: str, score: int = 0, reason: str = ""):
        self.start_time = start_time
        self.end_time = end_time
        self.title = title
        self.subtitle_text = subtitle_text
        self.duration = end_time - start_time
        self.score = score
        self.reason = reason


class SegmentDetector:
    """Phát hiện các đoạn video có ý nghĩa từ subtitle"""
    
    def __init__(self, min_duration: int = 50, max_duration: int = 179, min_pause: float = 4.0, 
                 max_pause_to_skip: float = 8.0, ai_api: Optional[OpenClawAI] = None, min_viral_score: int = 7):
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_pause = min_pause
        self.max_pause_to_skip = max_pause_to_skip
        self.ai_api = ai_api
        self.min_viral_score = min_viral_score
    
    def detect_segments(self, subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        if self.ai_api and self.ai_api.enabled:
            video_segments = self._detect_with_ai(subtitle_segments)
            if video_segments:
                return video_segments
            print("  ⚠️ AI không cắt được. Chuyển sang cắt tự động thông thường.")
        return self._detect_normal(subtitle_segments)
        
    def _detect_with_ai(self, subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        srt_text = ""
        for seg in subtitle_segments:
            srt_text += f"[{seg.start_time:.2f}s - {seg.end_time:.2f}s] {seg.text}\n"
        
        # Trừ đi 10s dự phòng cho việc giãn chữ cuối câu
        ai_results = self.ai_api.analyze_subtitles(srt_text, self.max_duration - 10)
        video_segments = []
        
        if ai_results:
            print(f"  ✨ Nhận kết quả từ AI, đang lọc độ Viral...")
            for item in ai_results:
                score = item.get('viral_score', 0)
                if score >= self.min_viral_score:
                    title = item.get('title', 'viral_segment').strip()
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    safe_title = safe_title.strip()
                    
                    hook_sentence = item.get('hook_sentence', '').strip()
                    print(f"     🔥 SIÊU PHẨM (Điểm: {score}/10): {title}")
                    if hook_sentence:
                        print(f"        🎣 Hook: {hook_sentence[:80]}...")
                    print(f"        ✏️ Lý do: {item.get('reason', '')}")
                    
                    start = float(item.get('start_time', 0))
                    end = float(item.get('end_time', 0))
                    
                    if hook_sentence:
                        hook_words = set(hook_sentence.lower().split())
                        best_match_score = 0
                        best_match_sub = None
                        search_window = [s for s in subtitle_segments if abs(s.start_time - start) <= 60]
                        for sub in search_window:
                            sub_words = set(sub.text.lower().split())
                            if not sub_words:
                                continue
                            overlap = len(hook_words & sub_words) / max(len(hook_words), 1)
                            if overlap > best_match_score:
                                best_match_score = overlap
                                best_match_sub = sub
                        if best_match_sub and best_match_score >= 0.3:
                            print(f"        📌 Đã căn chỉnh câu mở đầu: '{best_match_sub.text[:60]}...' (khớp {best_match_score:.0%})")
                            start = best_match_sub.start_time
                    
                    actual_text = [s.text for s in subtitle_segments if s.start_time >= start and s.end_time <= end]
                    
                    video_segments.append(VideoSegment(
                        start_time=start,
                        end_time=end,
                        title=safe_title,
                        subtitle_text=' '.join(actual_text),
                        score=score,
                        reason=item.get('reason', '')
                    ))
                else:
                    title = item.get('title', 'Đoạn không mang lại giá trị')
                    print(f"     ❌ Bỏ qua đoạn này vì điểm kém ({score}/10): {title}")

            if video_segments:
                # Sắp xếp theo score từ cao xuống thấp
                video_segments.sort(key=lambda x: x.score, reverse=True)
                return self._ensure_complete_sentences(video_segments, subtitle_segments)
        
        return []

    def _detect_normal(self, subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        """Phát hiện các đoạn có ý nghĩa từ subtitle (phương pháp dự phòng)"""
        video_segments = []
        
        if not subtitle_segments:
            return video_segments
        
        current_start = subtitle_segments[0].start_time
        current_texts = []
        last_end_time = subtitle_segments[0].end_time
        
        for i, seg in enumerate(subtitle_segments):
            pause_duration = seg.start_time - last_end_time if i > 0 else 0
            potential_duration = seg.end_time - current_start
            
            if pause_duration > self.max_pause_to_skip:
                if current_texts and (last_end_time - current_start) >= self.min_duration:
                    full_text = ' '.join(current_texts)
                    title = self._generate_title(full_text)
                    video_segments.append(VideoSegment(start_time=current_start, end_time=last_end_time, title=title, subtitle_text=full_text))
                    current_start = seg.start_time
                    current_texts = []
                else:
                    current_start = seg.start_time
                    current_texts = []
            
            should_cut = False
            if potential_duration > self.max_duration:
                should_cut = True
            elif potential_duration >= self.min_duration and pause_duration > self.min_pause:
                if current_texts and self._is_sentence_end(current_texts[-1]):
                    should_cut = True
            
            if should_cut and current_texts:
                full_text = ' '.join(current_texts)
                title = self._generate_title(full_text)
                video_segments.append(VideoSegment(start_time=current_start, end_time=last_end_time, title=title, subtitle_text=full_text))
                current_start = seg.start_time
                current_texts = []
            
            current_texts.append(seg.text)
            last_end_time = seg.end_time
        
        if current_texts:
            full_text = ' '.join(current_texts)
            title = self._generate_title(full_text)
            video_segments.append(VideoSegment(start_time=current_start, end_time=last_end_time, title=title, subtitle_text=full_text))
        
        return self._ensure_complete_sentences(video_segments, subtitle_segments)
    
    def _ensure_complete_sentences(self, video_segments: List[VideoSegment], 
                                   subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        """Đảm bảo mỗi đoạn KẾT THÚC ở câu hoàn chỉnh (không can thiệp đầu đoạn)"""
        corrected_segments = []
        
        for segment in video_segments:
            seg_subs = [s for s in subtitle_segments 
                       if s.start_time >= segment.start_time and s.end_time <= segment.end_time]
            
            if not seg_subs:
                corrected_segments.append(segment)
                continue
            
            # Kiểm tra câu cuối và đảm bảo đủ độ dài tối thiểu
            last_text = seg_subs[-1].text.strip()
            idx = subtitle_segments.index(seg_subs[-1])
            while (segment.end_time - segment.start_time < self.min_duration or not self._is_sentence_end(last_text)) and idx < len(subtitle_segments) - 1:
                next_sub = subtitle_segments[idx + 1]
                if next_sub.end_time - segment.start_time > self.max_duration:
                    break
                segment.end_time = next_sub.end_time
                seg_subs.append(next_sub)
                idx += 1
                last_text = seg_subs[-1].text.strip()
            
            # Giới hạn cứng thời gian
            while segment.end_time - segment.start_time > self.max_duration:
                if len(seg_subs) > 1:
                    seg_subs.pop()
                    segment.end_time = seg_subs[-1].end_time
                else:
                    segment.end_time = segment.start_time + self.max_duration
                    break
            
            segment.subtitle_text = ' '.join(s.text for s in seg_subs)
            segment.duration = segment.end_time - segment.start_time
            corrected_segments.append(segment)
        
        return corrected_segments
    
    @staticmethod
    def _is_sentence_end(text: str) -> bool:
        strong_endings = ['.', '?', '!', '。', '？', '！']
        return any(text.strip().endswith(ending) for ending in strong_endings)
    
    @staticmethod
    def _generate_title(text: str) -> str:
        cleaned = re.sub(r'[^\w\s]', '', text)
        words = cleaned.split()
        if not words: return 'segment'
        title = '_'.join(words[:10]).lower()
        return title[:120] if title else 'segment'


class VideoProcessor:
    """Xử lý video với FFmpeg"""
    
    def __init__(self, ffmpeg_path: str = 'ffmpeg'):
        self.ffmpeg_path = ffmpeg_path
    
    def process_video(
        self,
        input_video: str,
        output_video: str,
        start_time: float,
        end_time: float,
        title_text: str,
        logo_path: str,
        background_music: Optional[str] = None,
        music_volume: float = 0.15,
        zoom_factor: float = 1.15,
        watermark_path: Optional[str] = None
    ) -> bool:
        start_ts = self._format_timestamp(start_time)
        duration = end_time - start_time

        has_drawtext = True
        try:
            filters_check = subprocess.run([self.ffmpeg_path, '-filters'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if 'drawtext' not in filters_check.stdout:
                has_drawtext = False
        except:
            has_drawtext = False

        has_watermark_img = watermark_path and os.path.exists(watermark_path)

        filter_complex = (
            f"[0:v]format=yuv420p,scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=luma_radius=20:luma_power=3:chroma_radius=20:chroma_power=3,scale=1080:1920[bg];"
            f"[0:v]format=yuv420p,scale=1080*{zoom_factor}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
        )

        if has_drawtext:
            filter_complex += f"[v1];[v1]drawtext=text='PhatDaPhoTe.com':fontsize=36:fontcolor=white@0.8:x=(w-text_w)/2:y=h-100[v2];[v2][1:v]overlay=0:0[vout]"
        elif has_watermark_img:
            filter_complex += f"[v1];[v1][2:v]overlay=0:0[v2];[v2][1:v]overlay=0:0[vout]"
        else:
            filter_complex += f"[v1];[v1][1:v]overlay=0:0[vout]"
        
        cmd = [
            self.ffmpeg_path, '-hwaccel', 'auto', '-ss', start_ts, '-t', str(duration),
            '-i', input_video, '-i', logo_path
        ]
        
        input_count = 2
        if has_watermark_img and not has_drawtext:
            cmd.extend(['-i', watermark_path])
            input_count += 1
        
        audio_map = '0:a?'
        if background_music and os.path.exists(background_music):
            cmd.extend(['-stream_loop', '-1', '-i', background_music])
            bgm_idx = input_count
            filter_complex += f";[0:a?]volume=1.0[a1];[{bgm_idx}:a]volume={music_volume}[a2];[a1][a2]amix=inputs=2:duration=first[aout]"
            audio_map = '[aout]'
        
        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[vout]', '-map', audio_map,
            '-c:v', 'h264_nvenc', '-preset', 'p6', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k', '-shortest', '-y', output_video
        ])
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            print(f"     ❌ Lỗi: {e}")
            return False
    
    def _format_timestamp(self, seconds: float) -> str:
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class MainController:
    """Controller chính để điều phối toàn bộ quá trình"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.base_dir = Path(__file__).parent
        if self.base_dir.name == 'scripts':
            self.root_dir = self.base_dir.parent
        else:
            self.root_dir = self.base_dir

        self.input_dir = self.root_dir / 'input'
        self.output_dir = self.root_dir / 'output'
        
        # FFmpeg path
        if sys.platform == 'win32':
            # Tìm ở root_dir trước (nơi để ffmpeg.exe)
            ffmpeg_exe = self.root_dir / 'ffmpeg.exe'
            self.ffmpeg_path = str(ffmpeg_exe) if ffmpeg_exe.exists() else 'ffmpeg'
        else:
            hb_ffmpeg = Path('/opt/homebrew/bin/ffmpeg')
            self.ffmpeg_path = str(hb_ffmpeg) if hb_ffmpeg.exists() else 'ffmpeg'
            
        self.logo_path = self.root_dir / 'assets' / '9-16logo.png'
        self.config = self._load_config(config_path)
        
        # Background music
        music_cfg = self.config.get('background_music', {})
        if music_cfg.get('enabled', False):
            music_file = self.root_dir / 'assets' / music_cfg.get('file', 'nhacnen.mp3')
            self.background_music = str(music_file) if music_file.exists() else None
            self.music_volume = music_cfg.get('volume', 0.15)
        else:
            self.background_music = None
            self.music_volume = 0.15
        
        # AI Configuration (OpenClaw)
        ai_cfg = self.config.get('ai', {})
        provider = ai_cfg.get('provider', 'chiasegpu')
        provider_cfg = ai_cfg.get(provider, {})
        api_key = provider_cfg.get('api_key', '')
        
        if api_key:
            self.ai_api = OpenClawAI(api_key=api_key, enabled=True)
            self.min_viral_score = ai_cfg.get('min_viral_score', 7)
            print(f"[{provider.upper()} AI Enabled] Sẵn sàng tạo clip Viral.")
        else:
            self.ai_api = None
            self.min_viral_score = 7
        
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        config_file = self.root_dir / config_path
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"max_segment_duration": 179, "zoom_factor": 1.15}
    
    def find_video_subtitle_pairs(self) -> List[Tuple[Path, Path]]:
        pairs = []
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        
        # 1. Tìm trong các root folder input (file lẻ cùng tên)
        for f in self.input_dir.iterdir():
            if f.is_file() and f.suffix.lower() in video_exts:
                srt_file = f.with_suffix('.srt')
                if srt_file.exists():
                    pairs.append((f, srt_file))
        
        # 2. Tìm trong các subfolders (1 video + 1 srt dù tên gì)
        for subfolder in self.input_dir.iterdir():
            if subfolder.is_dir():
                video, srt = None, None
                for f in subfolder.iterdir():
                    if not video and f.suffix.lower() in video_exts: video = f
                    elif not srt and f.suffix.lower() == '.srt': srt = f
                
                if video and srt and (video, srt) not in pairs:
                    pairs.append((video, srt))
        return pairs
    
    def process_all(self):
        print("=" * 70)
        print("🎥 PHẦN MỀM CẮT VIDEO SHORT - CLAUDE AI EDITION")
        print("=" * 70)
        
        if not self.logo_path.exists():
            print(f"❌ Không tìm thấy logo tại: {self.logo_path}")
            return
        
        pairs = self.find_video_subtitle_pairs()
        if not pairs:
            print("❌ Không tìm thấy video + srt trong subfolders của input/")
            return
        
        print(f"✅ Tìm thấy {len(pairs)} video để xử lý\n")
        for video, srt in pairs:
            self.process_single_video(video, srt)
    
    def process_single_video(self, video_file: Path, subtitle_file: Path):
        print(f"📹 Xử lý: {video_file.name}")
        parser = SubtitleParser()
        subs = parser.parse_srt(str(subtitle_file))
        
        detector = SegmentDetector(
            min_duration=self.config.get('min_segment_duration', 50),
            max_duration=self.config.get('max_segment_duration', 179),
            ai_api=self.ai_api,
            min_viral_score=self.min_viral_score
        )
        segments = detector.detect_segments(subs)
        
        processor = VideoProcessor(self.ffmpeg_path)
        output_folder = self.output_dir / video_file.stem
        output_folder.mkdir(exist_ok=True)
        
        max_threads = self.config.get('max_threads', 3)
        print(f"  ⚡ Bắt đầu cắt {len(segments)} đoạn video (chạy {max_threads} luồng song song)...")
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_seg = {}
            for seg in segments:
                # Enforce strict 179s limit
                if seg.duration > 179:
                    seg.end_time = seg.start_time + 179
                    seg.duration = 179
                
                # Tên file sạch, giữ dấu cách để YouTube tự bắt tiêu đề đẹp
                clean_title = re.sub(r'[\\/*?:"<>|]', "", seg.title).strip()
                output_name = f"{clean_title}.mp4"
                output_path = output_folder / output_name
                
                future = executor.submit(
                    processor.process_video,
                    input_video=str(video_file),
                    output_video=str(output_path),
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    title_text=seg.title,
                    logo_path=str(self.logo_path),
                    watermark_path=str(self.root_dir / 'assets' / 'watermark.png'),
                    background_music=self.background_music,
                    music_volume=self.music_volume,
                    zoom_factor=self.config.get('zoom_factor', 1.5)
                )
                future_to_seg[future] = (seg, output_name)
                print(f"  🎬 Đã đưa vào tiến trình cắt: {seg.title} ({seg.duration:.1f}s)")
            
            for future in as_completed(future_to_seg):
                seg, output_name = future_to_seg[future]
                try:
                    success = future.result()
                    if success:
                        print(f"     ✅ Hoàn thành: {output_name}")
                    else:
                        print(f"     ❌ Lỗi khi cắt (FFMPEG error): {output_name}")
                except Exception as exc:
                    print(f"     ❌ Lỗi khi chạy luồng cho: {output_name} - {exc}")


def main():
    MainController().process_all()

if __name__ == '__main__':
    main()
