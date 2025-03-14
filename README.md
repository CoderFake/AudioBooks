# AudioBooks Project

Dự án AudioBooks bao gồm Backend Node.js và TTS Service FastAPI.

## Yêu cầu hệ thống

- Docker và Docker Compose
- Đối với Windows: Docker Desktop
- Đối với Linux/macOS: Docker Engine và Docker Compose

## Cách chạy dự án

### Windows

1. Tạo các thư mục cần thiết nếu chưa có:
   - `logs`
   - `temp/tts_temp`
   - `temp/tts_uploads`

2. Chạy script `start.bat`:
   ```
   start.bat
   ```

### Linux/macOS

1. Tạo các thư mục cần thiết:
   ```bash
   mkdir -p logs temp/tts_temp temp/tts_uploads
   ```

2. Cấp quyền thực thi cho script (nếu sử dụng script):
   ```bash
   chmod +x start.sh
   ```

3. Chạy script:
   ```bash
   ./start.sh
   ```

### Chạy trực tiếp với Docker Compose (tất cả hệ điều hành)

1. Sao chép file `.env.example` thành `.env` (nếu chưa có):
   ```
   cp .env.example .env
   ```

2. Chỉnh sửa các thông số trong file `.env` nếu cần

3. Khởi động dịch vụ:
   ```
   docker-compose up -d
   ```

4. Dừng dịch vụ:
   ```
   docker-compose down
   ```

## Các dịch vụ

- **Backend API**: http://localhost:3000
- **TTS Service API**: http://localhost:8000
- **MongoDB**: localhost:27017
- **MongoDB Admin UI**: http://localhost:8081

## Cấu trúc thư mục

```
AudioBooks/
├── BackEnd/            # Node.js Backend
├── tts-service/        # FastAPI TTS Service
docker-compose.yml      # Cấu hình Docker
init-mongo.js           # Script khởi tạo MongoDB
.env                    # Cấu hình môi trường
.env.example            # Mẫu cấu hình môi trường
start.bat               # Script khởi động cho Windows
start.sh                # Script khởi động cho Linux/macOS
```

## Ghi chú

- Các biến môi trường được đọc từ file `.env` trong thư mục gốc
- MongoDB được tự động khởi tạo với dữ liệu mẫu từ file `init-mongo.js`
- Đối với ứng dụng React Native, không cần cấu hình Docker, chỉ cần cập nhật URL API trong file cấu hình của ứng dụng

## Xử lý sự cố

- Nếu gặp lỗi kết nối MongoDB, kiểm tra cấu hình trong file `.env`
- Nếu Backend không khởi động, kiểm tra thư mục `AudioBooks/BackEnd` tồn tại và có file `package.json`
- Nếu TTS Service không khởi động, kiểm tra thư mục `AudioBooks/tts-service` tồn tại và có file `requirements.txt`