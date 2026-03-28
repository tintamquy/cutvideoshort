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
            
            prompt = f"""Bạn là một chuyên gia sáng tạo nội dung viral, giống như Vizard.ai. 
Hãy phân tích file phụ đề (subtitle) sau đây và chọn ra những phân đoạn có nội dung hấp dẫn, trọn vẹn ý nghĩa, có khả năng viral cao.

QUY TẮC BẮT BUỘC:
1. TÌM CÀNG NHIỀU ĐOẠN VIRAL CÀNG TỐT. Với video dài (như 30 phút - 1 tiếng), BẮT BUỘC phải tìm TẤT CẢ các đoạn tiềm năng. Đừng ngại trả về 10, 20, hay 30 đoạn nếu nội dung thật sự hấp dẫn. Tuyệt đối KHÔNG LƯỜI BIẾNG bỏ sót nội dung ở phần giữa hay phần cuối video. Giữ mọi thứ trong 1 file JSON duy nhất.
2. Độ dài mỗi đoạn BẮT BUỘC TỪ 120 GIÂY ĐẾN {max_duration} GIÂY (Từ 2 phút đến dưới 3 phút). Tuyệt đối không quá {max_duration} giây. Tự cộng/trừ thời gian cho mạch truyện trọn vẹn.
3. Tiêu đề (title): MỖI ĐOẠN CẦN CÓ Title tiếng Việt dạng Hook Title giật gân. RẤT QUAN TRỌNG: TIÊU ĐỀ PHẢI NGẮN GỌN (CHỈ TỪ 5 ĐẾN 8 TỪ).
4. Độ viral (viral_score): Chấm điểm 1 đến 10.
5. QUAN TRỌNG: Cột mốc thời gian trong ngoặc vuông [] được tính bằng TỔNG SỐ GIÂY (Ví dụ: [130.50s]). Khi trả JSON, BÊ NGUYÊN CON SỐ GIÂY NÀY VÀO `start_time` VÀ `end_time`. Tuyệt đối KHÔNG tự quy đổi lại thành phút, giây để tránh sai số hiển thị.
6. CHỈ TRẢ VỀ MỘT MẢNG JSON, KHÔNG BÌNH LUẬN GÌ THÊM.

Subtitles:
{subtitle_text}

Mẫu JSON TRẢ VỀ:
[
  {{
    "start_time": 120.50,
    "end_time": 215.00,
    "title": "Bí mật kiếm tiền triệu mỗi ngày mà không ai ngờ tới",
    "viral_score": 9,
    "reason": "Giải thích ngắn gọn 1 câu tiếng việt"
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
    def __init__(self, start_time: float, end_time: float, title: str, subtitle_text: str):
        self.start_time = start_time
        self.end_time = end_time
        self.title = title
        self.subtitle_text = subtitle_text
        self.duration = end_time - start_time


class SegmentDetector:
    """Phát hiện các đoạn video có ý nghĩa từ subtitle"""
    
    def __init__(self, min_duration: int = 55, max_duration: int = 150, min_pause: float = 4.0, 
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
            print("  ⚠️ AI không cắt được. Chuyển sang cắt tự động thông thường (bỏ qua chấm điểm viral).")
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
                    
                    print(f"     🔥 SIÊU PHẨM (Điểm: {score}/10): {title}")
                    print(f"        ✏️ Lý do: {item.get('reason', '')}")
                    
                    start = float(item.get('start_time', 0))
                    end = float(item.get('end_time', 0))
                    
                    actual_text = [s.text for s in subtitle_segments if s.start_time >= start and s.end_time <= end]
                    
                    video_segments.append(VideoSegment(
                        start_time=start,
                        end_time=end,
                        title=safe_title,
                        subtitle_text=' '.join(actual_text)
                    ))
                else:
                    title = item.get('title', 'Đoạn không đạt yêu cầu')
                    print(f"     ❌ Bỏ qua đoạn này vì điểm kém ({score}/10): {title}")

            if video_segments:
                return self._ensure_complete_sentences(video_segments, subtitle_segments)
        
        return []

    def _detect_normal(self, subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        """Phát hiện các đoạn có ý nghĩa từ subtitle, ĐẢM BẢO 100% video trong 55-150s"""
        video_segments = []
        
        if not subtitle_segments:
            return video_segments
        
        current_start = subtitle_segments[0].start_time
        current_texts = []
        last_end_time = subtitle_segments[0].end_time
        
        for i, seg in enumerate(subtitle_segments):
            # Tính khoảng cách với segment trước
            pause_duration = seg.start_time - last_end_time if i > 0 else 0
            
            # Tính duration nếu thêm segment này
            potential_duration = seg.end_time - current_start
            
            # Bỏ qua nếu khoảng trống quá dài (không có nội dung)
            if pause_duration > self.max_pause_to_skip:
                # Lưu đoạn hiện tại nếu có nội dung VÀ đủ dài
                if current_texts and (last_end_time - current_start) >= self.min_duration:
                    full_text = ' '.join(current_texts)
                    title = self._generate_title(full_text)
                    
                    video_segments.append(VideoSegment(
                        start_time=current_start,
                        end_time=last_end_time,
                        title=title,
                        subtitle_text=full_text
                    ))
                    
                    # Bắt đầu đoạn mới sau khoảng trống
                    current_start = seg.start_time
                    current_texts = []
                # Nếu đoạn quá ngắn, GIỮ LẠI và tiếp tục ghép
                elif current_texts:
                    # Không reset, tiếp tục ghép
                    pass
                else:
                    # Bắt đầu đoạn mới
                    current_start = seg.start_time
                    current_texts = []
            
            # Điều kiện cắt đoạn: ĐẢM BẢO 55-150s
            should_cut = False
            
            if potential_duration > self.max_duration:
                # VƯỢT QUÁ 150s - BẮT BUỘC PHẢI CẮT NGAY!
                # Tìm điểm cắt: ưu tiên câu kết thúc + pause
                if current_texts and self._is_sentence_end(current_texts[-1]) and pause_duration > 1.0:
                    should_cut = True
                elif pause_duration > 2.0:
                    # Pause đủ lớn thì cắt luôn
                    should_cut = True
                elif current_texts:
                    # Không có điều kiện tốt nhưng BẮT BUỘC phải cắt
                    should_cut = True
            elif potential_duration >= self.min_duration and pause_duration > self.min_pause:
                # Trong khoảng 55s-150s, chỉ cắt khi:
                # - Đã đủ min duration
                # - Có pause đủ lớn (>4s)
                # - VÀ câu kết thúc mạnh
                if current_texts and self._is_sentence_end(current_texts[-1]):
                    should_cut = True
            
            if should_cut and current_texts:
                # Tạo segment mới
                full_text = ' '.join(current_texts)
                title = self._generate_title(full_text)
                
                video_segments.append(VideoSegment(
                    start_time=current_start,
                    end_time=last_end_time,
                    title=title,
                    subtitle_text=full_text
                ))
                
                # Reset cho đoạn mới
                current_start = seg.start_time
                current_texts = []
            
            current_texts.append(seg.text)
            last_end_time = seg.end_time
        
        # Xử lý đoạn cuối cùng
        if current_texts:
            final_duration = last_end_time - current_start
            
            # Nếu đoạn cuối < min_duration, gộp vào đoạn trước
            if final_duration < self.min_duration and len(video_segments) > 0:
                # Gộp vào đoạn trước
                last_segment = video_segments[-1]
                combined_text = last_segment.subtitle_text + ' ' + ' '.join(current_texts)
                combined_title = self._generate_title(combined_text)
                
                # Cập nhật đoạn cuối
                video_segments[-1] = VideoSegment(
                    start_time=last_segment.start_time,
                    end_time=last_end_time,
                    title=combined_title,
                    subtitle_text=combined_text
                )
            else:
                # Đủ dài, thêm như đoạn độc lập
                full_text = ' '.join(current_texts)
                title = self._generate_title(full_text)
                
                video_segments.append(VideoSegment(
                    start_time=current_start,
                    end_time=last_end_time,
                    title=title,
                    subtitle_text=full_text
                ))
        
        # ĐẢM BẢO CÂU ĐẦU/CUỐI TRỌN VẸN
        video_segments = self._ensure_complete_sentences(video_segments, subtitle_segments)
        
        return video_segments
    
    def _ensure_complete_sentences(self, video_segments: List[VideoSegment], 
                                   subtitle_segments: List[SubtitleSegment]) -> List[VideoSegment]:
        """Đảm bảo mỗi đoạn BẮT ĐẦU và KẾT THÚC ở câu hoàn chỉnh"""
        corrected_segments = []
        
        for seg_idx, segment in enumerate(video_segments):
            # Tìm subtitle segments trong khoảng này
            seg_subs = [s for s in subtitle_segments 
                       if s.start_time >= segment.start_time and s.end_time <= segment.end_time]
            
            if not seg_subs:
                corrected_segments.append(segment)
                continue
            
            # Kiểm tra câu đầu tiên: Nếu không bắt đầu bằng chữ hoa, mở rộng ra trước
            first_text = seg_subs[0].text.strip()
            idx = subtitle_segments.index(seg_subs[0])
            while first_text and not first_text[0].isupper() and not first_text[0].isdigit() and idx > 0:
                prev_sub = subtitle_segments[idx - 1]
                if segment.end_time - prev_sub.start_time > self.max_duration:
                    break
                segment.start_time = prev_sub.start_time
                seg_subs.insert(0, prev_sub)
                idx -= 1
                first_text = seg_subs[0].text.strip()
            
            # Kiểm tra câu cuối: Nếu không kết thúc bằng dấu chấm câu, mở rộng ra sau
            last_text = seg_subs[-1].text.strip()
            idx = subtitle_segments.index(seg_subs[-1])
            while not self._is_sentence_end(last_text) and idx < len(subtitle_segments) - 1:
                next_sub = subtitle_segments[idx + 1]
                if next_sub.end_time - segment.start_time > self.max_duration:
                    break
                segment.end_time = next_sub.end_time
                seg_subs.append(next_sub)
                idx += 1
                last_text = seg_subs[-1].text.strip()
            
            # --- CHẶN CỨNG THỜI LƯỢNG KỊCH TRẦN ---
            # Nếu AI vẫn lỳ lợm nhả khoảng thời gian > max_duration (VD 190s),
            # bắt buộc phải cắt bỏ các dòng phụ đề cuối cùng cho đến khi < max_duration
            while segment.end_time - segment.start_time > self.max_duration:
                if len(seg_subs) > 1:
                    seg_subs.pop()
                    segment.end_time = seg_subs[-1].end_time
                else:
                    segment.end_time = segment.start_time + self.max_duration
                    break
            
            # Tinh chỉnh mềm: Sau khi lùi xuống dưới mức max_duration, 
            # dò lùi tiếp để tìm một "dấu chấm câu" nhằm giữ mạch truyện trọn vẹn nhất có thể.
            while len(seg_subs) > 1 and not self._is_sentence_end(seg_subs[-1].text.strip()):
                last_end = seg_subs[-2].end_time
                if last_end - segment.start_time <= self.min_duration:
                    break   # Dừng dò lùi lại vì video chạm ngưỡng quá ngắn
                seg_subs.pop()
                segment.end_time = seg_subs[-1].end_time
                
            # Cập nhật subtitle text
            segment.subtitle_text = ' '.join(s.text for s in seg_subs)
            if not getattr(self, 'ai_api', None) or getattr(self.ai_api, 'enabled', False) == False:
                segment.title = self._generate_title(segment.subtitle_text)
            segment.duration = segment.end_time - segment.start_time
            
            corrected_segments.append(segment)
        
        return corrected_segments
    
    @staticmethod
    def _is_sentence_end(text: str) -> bool:
        """Kiểm tra xem văn bản có kết thúc bằng dấu câu mạnh không"""
        strong_endings = ['.', '?', '!', '。', '？', '！']
        return any(text.strip().endswith(ending) for ending in strong_endings)
    
    @staticmethod
    def _generate_title(text: str) -> str:
        """Tạo title CÓ Ý NGHĨA TỔNG QUÁT từ nội dung đoạn"""
        # Loại bỏ ký tự đặc biệt nhưng giữ dấu cách
        cleaned = re.sub(r'[^\w\s]', '', text)
        cleaned = ' '.join(cleaned.split())
        
        # Tách thành các từ
        words = cleaned.split()
        
        if len(words) == 0:
            return 'segment'
        
        # Chiến lược: lấy từ 10-15 từ để phản ánh ý nghĩa tổng quát
        # Ưu tiên: đầu + giữa để bắt được chủ đề chính
        if len(words) <= 15:
            # Ngắn, lấy hết
            selected_words = words
        else:
            # Dài: lấy 8 từ đầu (chủ đề) + 4-7 từ ở giữa (nội dung chính)
            start_words = words[:8]
            mid_point = len(words) // 2
            mid_words = words[mid_point:mid_point+7]
            selected_words = start_words + mid_words
            selected_words = selected_words[:15]  # Giới hạn 15 từ
        
        title = '_'.join(selected_words).lower()
        
        # Giới hạn độ dài 120 ký tự
        if len(title) > 120:
            title = title[:120]
        
        return title if title else 'segment'


class VideoProcessor:
    """Xử lý video với FFmpeg"""
    
    def __init__(self, ffmpeg_path: str = 'ffmpeg.exe'):
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
        zoom_factor: float = 1.15
    ) -> bool:
        """
        Xử lý video: cắt, chuyển 16:9 -> 9:16, thêm blur bg, watermark, logo, nhạc nền
        
        Args:
            input_video: Đường dẫn video input
            output_video: Đường dẫn video output
            start_time: Thời điểm bắt đầu (giây)
            end_time: Thời điểm kết thúc (giây)
            title_text: Text cho tên file (không dùng trong video)
            logo_path: Đường dẫn logo overlay
            background_music: Đường dẫn file nhạc nền (optional)
            music_volume: Âm lượng nhạc nền (0.0-1.0, default 0.15)
            zoom_factor: Hệ số zoom (1.1 = zoom 10%, 1.2 = zoom 20%)
        """
        
        # Format timestamps
        start_ts = self._format_timestamp(start_time)
        duration = end_time - start_time
        
        # Build FFmpeg filter_complex
        # 1. Blur background layer
        # 2. Zoom & crop video chính
        # 3. Overlay video lên background
        # 4. Thêm watermark
        # 5. Overlay logo
        
        filter_complex = (
            # Layer 1: Blur background (scale + blur)
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,gblur=sigma=30[bg];"
            
            # Layer 2: Video chính - zoom và crop để vuông hơn
            f"[0:v]scale=iw*{zoom_factor}:ih*{zoom_factor},"
            f"crop=ih*9/16:ih,"  # Crop để tỷ lệ 9:16
            f"scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            
            # Layer 3: Overlay video lên background
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v1];"
            
            # Layer 4: Thêm watermark "PhatDaPhoTe.com" ở dưới
            f"[v1]drawtext=text='PhatDaPhoTe.com':"
            f"fontsize=36:fontcolor=white@0.8:x=(w-text_w)/2:y=h-100[v2];"
            
            # Layer 5: Overlay logo (file PNG đã có sẵn tỷ lệ 9:16)
            f"[v2][1:v]overlay=0:0[vout]"
        )
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            '-ss', start_ts,  # Seek đến vị trí bắt đầu
            '-t', str(duration),  # Duration
            '-i', input_video,  # Input video
            '-i', logo_path,  # Input logo
        ]
        
        # Thêm nhạc nền nếu có
        audio_map = '0:a?'  # Audio từ video gốc
        if background_music and os.path.exists(background_music):
            cmd.extend(['-stream_loop', '-1', '-i', background_music])  # Loop nhạc nền
            # Mix audio: video gốc (100%) + nhạc nền (volume)
            filter_complex += f";[0:a?]volume=1.0[a1];[2:a]volume={music_volume}[a2];[a1][a2]amix=inputs=2:duration=first[aout]"
            audio_map = '[aout]'
        
        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[vout]',  # Map video output
            '-map', audio_map,  # Map audio output
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Encoding preset
            '-crf', '23',  # Quality
            '-c:a', 'aac',  # Audio codec
            '-b:a', '128k',  # Audio bitrate
            '-shortest',  # Kết thúc khi stream ngắn nhất kết thúc
            '-y',  # Overwrite output
            output_video
        ])
        
        print(f"  🎬 Đang xử lý: {os.path.basename(output_video)}")
        print(f"     ⏱️  {self._format_timestamp(start_time)} -> {self._format_timestamp(end_time)} ({duration:.1f}s)")
        
        try:
            # Chạy FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                print(f"     ✅ Hoàn thành!")
                return True
            else:
                print(f"     ❌ Lỗi FFmpeg:")
                print(result.stderr.decode('utf-8', errors='ignore'))
                return False
                
        except Exception as e:
            print(f"     ❌ Lỗi: {e}")
            return False
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Chuyển giây thành format HH:MM:SS.mmm"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    @staticmethod
    def _escape_text(text: str) -> str:
        """Escape text cho FFmpeg drawtext filter"""
        # FFmpeg drawtext cần escape các ký tự đặc biệt
        text = text.replace('\\', '\\\\')
        text = text.replace("'", "\\'")
        text = text.replace(':', '\\:')
        return text


class MainController:
    """Controller chính để điều phối toàn bộ quá trình"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.base_dir = Path(__file__).parent
        self.input_dir = self.base_dir / 'input'
        self.output_dir = self.base_dir / 'output'
        
        # Hỗ trợ ffmpeg đa nền tảng (Mac / Win)
        if sys.platform == 'win32':
            self.ffmpeg_path = self.base_dir / 'ffmpeg.exe'
        else:
            local_ff = self.base_dir / 'ffmpeg'
            self.ffmpeg_path = local_ff if local_ff.exists() else Path('ffmpeg')
            
        self.logo_path = self.base_dir / '9-16logo.png'
        
        # Load config
        self.config = self._load_config(config_path)
        
        # Background music
        music_cfg = self.config.get('background_music', {})
        if music_cfg.get('enabled', False):
            music_file = self.base_dir / music_cfg.get('file', 'nhacnen.mp3')
            self.background_music = str(music_file) if music_file.exists() else None
            self.music_volume = music_cfg.get('volume', 0.15)
        else:
            self.background_music = None
            self.music_volume = 0.15
        
        # OpenClaw AI
        ai_cfg = self.config.get('openclaw_ai', {})
        if ai_cfg.get('enabled', False) and ai_cfg.get('api_key'):
            self.ai_api = OpenClawAI(api_key=ai_cfg['api_key'], model=ai_cfg.get('model', 'claude-haiku-4.5'), enabled=True)
            self.min_viral_score = ai_cfg.get('min_viral_score', 7)
        else:
            self.ai_api = None
            self.min_viral_score = 7
        
        # Tạo directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load config hoặc tạo mặc định"""
        default_config = {
            "max_segment_duration": 120,
            "min_pause_duration": 2.0,
            "zoom_factor": 1.15
        }
        
        config_file = self.base_dir / config_path
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Lỗi load config: {e}, dùng config mặc định")
                return default_config
        else:
            # Tạo config mặc định
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def find_video_subtitle_pairs(self) -> List[Tuple[Path, Path]]:
        """Tìm trong mỗi folder con của input, lấy 1 video và 1 srt dù tên gì"""
        pairs = []
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        
        for folder in self.input_dir.iterdir():
            if folder.is_dir():
                videos = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]
                srts = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == '.srt']
                
                if videos and srts:
                    pairs.append((videos[0], srts[0]))
                else:
                    if not videos:
                        print(f"⚠️ Thư mục con '{folder.name}' bị thiếu video.")
                    if not srts:
                        print(f"⚠️ Thư mục con '{folder.name}' thiếu file subtitle (.srt).")
                        
        return pairs
    
    def process_all(self):
        """Xử lý tất cả video trong input folder"""
        print("=" * 70)
        print("🎥 PHẦN MỀM CẮT VIDEO SHORT - (Chế Độ Vizard AI)")
        print("=" * 70)
        print()
        if self.ai_api and self.ai_api.enabled:
            print(f"🤖 Chế độ AI Tự động quyết định cắt: ĐÃ BẬT")
            print(f"   - API: OpenClaw (Chi tiết model: {self.ai_api.model})")
            print(f"   - Viral Score tổi thiểu: {self.min_viral_score}/10")
        else:
            print("⚡ Chế độ cắt nhanh thông thường: ĐÃ BẬT (AI Đang Tắt)")
        print()
        
        # Hỏi người dùng về nhạc nền
        music_cfg = self.config.get('background_music', {})
        default_enabled = music_cfg.get('enabled', False)
        default_str = "CÓ" if default_enabled else "KHÔNG"
        
        print(f"🎵 Cấu hình nhạc nền hiện tại: {default_str}")
        user_input = input(f"👉 Bạn có muốn chèn nhạc nền không? (y=Có, n=Không, Enter=Giữ nguyên): ").strip().lower()

        if user_input == 'n':
            self.background_music = None
            print("🔕 Đã TẮT nhạc nền cho lần chạy này.")
        elif user_input == 'y':
            # Try to enable
            music_file_name = music_cfg.get('file', 'nhacnen.mp3')
            music_file = self.base_dir / music_file_name
            if music_file.exists():
                self.background_music = str(music_file)
                self.music_volume = music_cfg.get('volume', 0.15)
                print(f"🎵 Đã BẬT nhạc nền: {music_file_name}")
            else:
                print(f"❌ Không tìm thấy file nhạc '{music_file_name}'! Sẽ không chèn nhạc.")
                self.background_music = None
        else:
            print(f"⏩ Giữ nguyên cấu hình: {default_str}")
            
        print()
        
        # Kiểm tra FFmpeg (qua file hoặc biến PATH macOS)
        if not shutil.which(str(self.ffmpeg_path)):
            print("❌ Không tìm thấy ffmpeg trong hệ thống hoặc thư mục!")
            input("Nhấn Enter để thoát...")
            return
        
        # Kiểm tra logo
        if not self.logo_path.exists():
            print("❌ Không tìm thấy 9-16logo.png!")
            input("Nhấn Enter để thoát...")
            return
        
        # Tìm video pairs
        pairs = self.find_video_subtitle_pairs()
        
        if not pairs:
            print("❌ Không tìm thấy video + subtitle nào trong folder 'input'!")
            print("📁 Vui lòng đặt video (.mp4) và subtitle (.srt) cùng tên vào folder 'input'")
            input("Nhấn Enter để thoát...")
            return
        
        print(f"✅ Tìm thấy {len(pairs)} video để xử lý\n")
        
        # Xử lý từng video
        for idx, (video_file, subtitle_file) in enumerate(pairs, 1):
            print(f"[{idx}/{len(pairs)}] 📹 {video_file.name}")
            print(f"           📝 {subtitle_file.name}")
            print()
            
            self.process_single_video(video_file, subtitle_file)
            print()
        
        print("=" * 70)
        print("✅ HOÀN THÀNH TẤT CẢ!")
        print("=" * 70)
        input("Nhấn Enter để thoát...")
    
    def process_single_video(self, video_file: Path, subtitle_file: Path):
        """Xử lý một video"""
        # Parse subtitle
        print("  📖 Đang phân tích subtitle...")
        parser = SubtitleParser()
        subtitle_segments = parser.parse_srt(str(subtitle_file))
        print(f"     ✅ Đọc được {len(subtitle_segments)} đoạn subtitle")
        
        # Phát hiện segments
        print("  🔍 Đang phát hiện các đoạn có ý nghĩa...")
        detector = SegmentDetector(
            min_duration=self.config.get('min_segment_duration', 50),
            max_duration=self.config['max_segment_duration'],
            min_pause=self.config['min_pause_duration'],
            ai_api=self.ai_api,
            min_viral_score=self.min_viral_score
        )
        video_segments = detector.detect_segments(subtitle_segments)
        print(f"     ✅ Phát hiện được {len(video_segments)} đoạn short")
        print()
        
        # Tạo output folder
        output_folder = self.output_dir / video_file.stem
        output_folder.mkdir(exist_ok=True)
        
        # Xử lý từng segment
        processor = VideoProcessor(str(self.ffmpeg_path))
        
        success_count = 0
        for idx, segment in enumerate(video_segments, 1):
            base_name = segment.title if segment.title else f"Short_{idx:02d}"
            output_filename = f"{base_name}.mp4"
            output_path = output_folder / output_filename
            # Nếu trùng tên file, thêm index
            counter = 1
            while output_path.exists():
                output_filename = f"{base_name} ({counter}).mp4"
                output_path = output_folder / output_filename
                counter += 1
            
            success = processor.process_video(
                input_video=str(video_file),
                output_video=str(output_path),
                start_time=segment.start_time,
                end_time=segment.end_time,
                title_text=segment.title.title(),
                logo_path=str(self.logo_path),
                background_music=self.background_music,
                music_volume=self.music_volume,
                zoom_factor=self.config['zoom_factor']
            )
            
            if success:
                success_count += 1
        
        print()
        print(f"  🎉 Hoàn thành: {success_count}/{len(video_segments)} đoạn")
        print(f"  📁 Output: {output_folder}")


def main():
    """Entry point"""
    controller = MainController()
    controller.process_all()


if __name__ == '__main__':
    main()
