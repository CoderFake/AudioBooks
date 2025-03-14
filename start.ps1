# PowerShell script cho Windows (chạy với quyền cao hơn)

# Tạo thư mục cần thiết
New-Item -ItemType Directory -Path "logs" -Force | Out-Null
New-Item -ItemType Directory -Path "temp\tts_temp" -Force | Out-Null
New-Item -ItemType Directory -Path "temp\tts_uploads" -Force | Out-Null

# Kiểm tra file .env
if (-not (Test-Path ".env")) {
    Write-Host "File .env không tồn tại. Đang tạo file từ mẫu..."

    if (Test-Path ".env.example") {
        Copy-Item ".env.example" -Destination ".env"
    } else {
        Write-Host "Không tìm thấy file .env.example, đang tạo file .env mới."
        @"
# Host Configuration
HOST_NAME=localhost
EXTERNAL_HOST=0.0.0.0

# MongoDB Configuration
MONGO_USERNAME=admin
MONGO_PASSWORD=123456
MONGO_DATABASE=audiobooksDB
MONGO_PORT=27017
MONGO_EXPRESS_PORT=8081
MONGO_EXPRESS_USER=user
MONGO_EXPRESS_PASSWORD=password

# Backend Configuration
BACKEND_PORT=3000
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=30d
EMAIL_NAME=your_email@gmail.com
EMAIL_PASS=your_email_app_password
OTP_SECRET=your_otp_secret_key_here

# TTS Service Configuration
TTS_PORT=8000
DEBUG=True
PROJECT_NAME=TTS Service
TTS_SECRET_KEY=your_secret_key_here
DEFAULT_VOICE_MODEL=female
CHUNK_SIZE=5000

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email
FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
"@ | Out-File -FilePath ".env" -Encoding utf8
    }

    Write-Host "File .env đã được tạo. Vui lòng chỉnh sửa cấu hình phù hợp."
    Write-Host "Nhấn Enter để tiếp tục hoặc Ctrl+C để thoát và chỉnh sửa file .env..."
    Read-Host
}

# Kiểm tra docker đã cài đặt chưa
try {
    docker --version | Out-Null
} catch {
    Write-Host "Docker chưa được cài đặt. Vui lòng cài đặt Docker và Docker Compose."
    exit 1
}

# Kiểm tra docker-compose đã cài đặt chưa
try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "Docker Compose chưa được cài đặt. Vui lòng cài đặt Docker Compose."
    exit 1
}

function Show-Menu {
    Clear-Host
    Write-Host "=== AudioBooks Management ==="
    Write-Host "1. Khởi động tất cả dịch vụ"
    Write-Host "2. Dừng tất cả dịch vụ"
    Write-Host "3. Khởi động lại tất cả dịch vụ"
    Write-Host "4. Xem logs"
    Write-Host "5. Xóa tất cả dữ liệu và khởi động lại (cẩn thận!)"
    Write-Host "6. Thoát"
    Write-Host ""

    $choice = Read-Host "Nhập lựa chọn của bạn (1-6)"

    switch ($choice) {
        "1" {
            Write-Host "Đang khởi động tất cả dịch vụ..."
            docker-compose up -d
            Write-Host "Tất cả dịch vụ đã được khởi động."
            Write-Host "Backend API: http://localhost:3000"
            Write-Host "TTS Service API: http://localhost:8000"
            Write-Host "MongoDB Admin UI: http://localhost:8081"
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "2" {
            Write-Host "Đang dừng tất cả dịch vụ..."
            docker-compose down
            Write-Host "Tất cả dịch vụ đã được dừng."
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "3" {
            Write-Host "Đang khởi động lại tất cả dịch vụ..."
            docker-compose restart
            Write-Host "Tất cả dịch vụ đã được khởi động lại."
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "4" {
            Write-Host "Đang hiển thị logs (Ctrl+C để thoát)..."
            docker-compose logs -f
            Show-Menu
        }
        "5" {
            Write-Host "CẢNH BÁO: Thao tác này sẽ xóa tất cả dữ liệu Docker hiện có của dự án!"
            $confirm = Read-Host "Bạn có chắc chắn muốn tiếp tục? (y/n)"
            if ($confirm -eq "y") {
                Write-Host "Đang xóa dữ liệu và containers..."
                docker-compose down -v
                docker-compose up -d
                Write-Host "Dữ liệu đã được xóa và dịch vụ đã được khởi động lại."
            } else {
                Write-Host "Đã hủy thao tác."
            }
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "6" {
            Write-Host "Thoát."
            exit 0
        }
        default {
            Write-Host "Lựa chọn không hợp lệ."
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
    }
}

Show-Menu