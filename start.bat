@echo off
echo === AudioBooks Services Starter ===

REM Tạo thư mục cần thiết
mkdir logs 2>nul
mkdir temp\tts_temp 2>nul
mkdir temp\tts_uploads 2>nul

REM Kiểm tra file .env
if not exist .env (
    echo File .env không tồn tại. Đang tạo file từ mẫu...
    copy .env.example .env >nul 2>&1
    if not exist .env (
        echo Không tìm thấy file .env.example, đang tạo file .env mới.
        echo # Host Configuration > .env
        echo HOST_NAME=localhost >> .env
        echo EXTERNAL_HOST=0.0.0.0 >> .env
        echo. >> .env
        echo # MongoDB Configuration >> .env
        echo MONGO_USERNAME=admin >> .env
        echo MONGO_PASSWORD=123456 >> .env
        echo MONGO_DATABASE=audiobooksDB >> .env
        echo MONGO_PORT=27017 >> .env
        echo MONGO_EXPRESS_PORT=8081 >> .env
        echo MONGO_EXPRESS_USER=user >> .env
        echo MONGO_EXPRESS_PASSWORD=password >> .env
        echo. >> .env
        echo # Backend Configuration >> .env
        echo BACKEND_PORT=3000 >> .env
        echo JWT_SECRET=your_jwt_secret_key_here >> .env
        echo JWT_EXPIRES_IN=30d >> .env
        echo EMAIL_NAME=your_email@gmail.com >> .env
        echo EMAIL_PASS=your_email_app_password >> .env
        echo OTP_SECRET=your_otp_secret_key_here >> .env
        echo. >> .env
        echo # TTS Service Configuration >> .env
        echo TTS_PORT=8000 >> .env
        echo DEBUG=True >> .env
        echo PROJECT_NAME=TTS Service >> .env
        echo TTS_SECRET_KEY=your_secret_key_here >> .env
        echo DEFAULT_VOICE_MODEL=female >> .env
        echo CHUNK_SIZE=5000 >> .env
        echo. >> .env
        echo # Firebase Configuration >> .env
        echo FIREBASE_PROJECT_ID=your-firebase-project-id >> .env
        echo FIREBASE_PRIVATE_KEY=your-firebase-private-key >> .env
        echo FIREBASE_CLIENT_EMAIL=your-firebase-client-email >> .env
        echo FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket >> .env
    )
    echo File .env đã được tạo. Vui lòng chỉnh sửa cấu hình phù hợp.
    echo Nhấn Enter để tiếp tục hoặc Ctrl+C để thoát và chỉnh sửa file .env...
    pause >nul
)

REM Kiểm tra docker đã cài đặt chưa
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker chưa được cài đặt. Vui lòng cài đặt Docker và Docker Compose.
    exit /b 1
)

REM Kiểm tra docker-compose đã cài đặt chưa
docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker Compose chưa được cài đặt. Vui lòng cài đặt Docker Compose.
    exit /b 1
)

:menu
cls
echo === AudioBooks Management ===
echo 1. Khởi động tất cả dịch vụ
echo 2. Dừng tất cả dịch vụ
echo 3. Khởi động lại tất cả dịch vụ
echo 4. Xem logs
echo 5. Xóa tất cả dữ liệu và khởi động lại (cẩn thận!)
echo 6. Thoát
echo.
set /p choice=Nhập lựa chọn của bạn (1-6):

if "%choice%"=="1" (
    echo Đang khởi động tất cả dịch vụ...
    docker-compose up -d
    echo Tất cả dịch vụ đã được khởi động.
    echo Backend API: http://localhost:3000
    echo TTS Service API: http://localhost:8000
    echo MongoDB Admin UI: http://localhost:8081
    pause
    goto menu
)

if "%choice%"=="2" (
    echo Đang dừng tất cả dịch vụ...
    docker-compose down
    echo Tất cả dịch vụ đã được dừng.
    pause
    goto menu
)

if "%choice%"=="3" (
    echo Đang khởi động lại tất cả dịch vụ...
    docker-compose restart
    echo Tất cả dịch vụ đã được khởi động lại.
    pause
    goto menu
)

if "%choice%"=="4" (
    echo Đang hiển thị logs (Ctrl+C để thoát)...
    docker-compose logs -f
    goto menu
)

if "%choice%"=="5" (
    echo CẢNH BÁO: Thao tác này sẽ xóa tất cả dữ liệu Docker hiện có của dự án!
    set /p confirm=Bạn có chắc chắn muốn tiếp tục? (y/n):
    if /i "%confirm%"=="y" (
        echo Đang xóa dữ liệu và containers...
        docker-compose down -v
        docker-compose up -d
        echo Dữ liệu đã được xóa và dịch vụ đã được khởi động lại.
    ) else (
        echo Đã hủy thao tác.
    )
    pause
    goto menu
)

if "%choice%"=="6" (
    echo Thoát.
    exit /b 0
)

echo Lựa chọn không hợp lệ.
pause
goto menu