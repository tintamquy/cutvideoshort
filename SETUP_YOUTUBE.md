# Hướng Dẫn Tích Hợp YouTube Data API v3 (Auto Upload)

Để phần mềm có quyền thay mặt bạn đăng tải video tự động lên kênh YouTube, bạn cần cung cấp một tệp cấp quyền tên là `client_secrets.json` từ hệ thống của Google. Dưới đây là các bước chi tiết (100% miễn phí):

## Bước 1: Tạo Dự Án Trên Google Cloud

1. Truy cập vào trang quản trị của Google Coud: [Google Cloud Console](https://console.cloud.google.com/).
2. Đăng nhập bằng chính tài khoản Gmail đang quản lý kênh YouTube của bạn.
3. Nhìn lên góc trên bên trái (cạnh logo Google Cloud), click vào mũi tên xổ xuống chọn **"Select a project"** (Chọn dự án) hoặc chữ **"New Project"** (Dự án mới).
4. Nhập tên dự án (Ví dụ: `Auto Upload YouTube Shorts`) và bấm **Create** (Tạo).

## Bước 2: Kích Hoạt (Enable) YouTube Data API v3

1. Đợi dự án tạo xong (sẽ có thông báo ở góc phải trên cùng), đảm bảo bạn đang chọn đúng dự án vừa tạo.
2. Trên thanh tìm kiếm ở giữa trên cùng, gõ **"YouTube Data API v3"** và chọn kết quả đầu tiên hiện ra.
3. Click vào nút **"Enable"** (Bật) màu xanh dương.

## Bước 3: Thiết Lập Màn Hình Xin Quyền (OAuth Consent Screen)

Để tool Python của bạn xin quyền truy cập, bạn cần thiết lập màn hình xin quyền:
1. Ở thanh menu bên trái, tìm đến **"APIs & Services"** (API và Dịch vụ) → Chọn **"OAuth consent screen"** (Màn hình xin phép...).
2. Tại phần User Type (Loại người dùng), chọn **"External"** (Bên ngoài) và bấm **Create** (Tạo).
3. Điền thông tin bắt buộc:
   - **App name**: Đặt tên bất kỳ (Ví dụ: `My Shorts Uploader`).
   - **User support email**: Chọn email của chính bạn.
   - Kéo xuống dưới cùng phần **Developer contact information**: Nhập lại email của bạn.
   - Nhấn **Save and Continue** (Lưu và tiếp tục).
4. Các bước tiếp theo (Scopes) cứ nhấn **Save and Continue** bỏ qua.
5. Tại bảng **Test users** (Người dùng thử nghiệm): Nhấn nút **"+ ADD USERS"**, nhập ĐÚNG địa chỉ email YouTube của bạn vào và nhấn Save. (Nếu không thêm, ứng dụng sẽ báo lỗi khi bạn đăng nhập).
6. Bấm **Save and Continue** rồi về trang Dashboard.

## Bước 4: Tạo Thông Tin Xác Thực và Tải File `client_secrets.json`

1. Vẫn ở menu bên trái mục **"APIs & Services"**, bấm vào **"Credentials"** (Thông tin xác thực).
2. Nhấn nút **"+ CREATE CREDENTIALS"** (Tạo thông tin xác thực) ở giữa màn hình phía trên → Chọn **"OAuth client ID"**.
3. Tại ô **Application type** (Loại ứng dụng), xổ xuống chọn **"Desktop App"** (Ứng dụng cho máy tính để bàn).
4. Đặt tên (ví dụ: `Python Uploader`) và nhấn **Create** (Tạo).
5. Một cửa sổ hiện ra báo thành công. Nhấn vào nút **"DOWNLOAD JSON"** (Tải tệp JSON xuống).
6. Đổi tên tệp vừa tải xuống thành **`client_secrets.json`** và copy (dán) nó vào trong thư mục dự án `d:\Projects\Cut-Short-Video` của bạn (Cùng chỗ với file `run.bat`).

*(Xong! Khi bạn hoàn tất, hãy nhắn để tôi cung cấp cho bạn file `youtube_upload.py` hướng dẫn tool tự động ghép nối và đăng lịch nhé!)*
