#!/bin/bash

# Kiểm tra file .env
if [ ! -f .env ]; then
    echo "File .env không tồn tại. Vui lòng sao chép từ .env.example và điền thông tin cần thiết."
    echo "cp .env.example .env"
    exit 1
fi

# Tạo các thư mục cần thiết
mkdir -p logs
mkdir -p /tmp/tts_temp
mkdir -p /tmp/tts_uploads

# Kiểm tra Docker đã cài đặt chưa
if ! command -v docker &> /dev/null; then
    echo "Docker chưa được cài đặt. Vui lòng cài đặt Docker và Docker Compose."
    exit 1
fi

# Kiểm tra Docker Compose đã cài đặt chưa
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose chưa được cài đặt. Vui lòng cài đặt Docker Compose."
    exit 1
fi

# Hiển thị menu
echo "=== TTS Service Management ==="
echo "1. Khởi động dịch vụ"
echo "2. Dừng dịch vụ"
echo "3. Xem logs"
echo "4. Khởi động lại dịch vụ"
echo "5. Xây dựng lại containers"
echo "6. Thoát"
echo -n "Nhập lựa chọn của bạn (1-6): "
read choice

case $choice in
    1)
        echo "Đang khởi động dịch vụ..."
        docker-compose up -d
        echo "Dịch vụ đã được khởi động. API có thể truy cập tại: http://localhost:8000"
        echo "MongoDB Admin UI có thể truy cập tại: http://localhost:8081"
        ;;
    2)
        echo "Đang dừng dịch vụ..."
        docker-compose down
        echo "Dịch vụ đã được dừng."
        ;;
    3)
        echo "Đang hiển thị logs..."
        docker-compose logs -f
        ;;
    4)
        echo "Đang khởi động lại dịch vụ..."
        docker-compose restart
        echo "Dịch vụ đã được khởi động lại."
        ;;
    5)
        echo "Đang xây dựng lại containers..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "Containers đã được xây dựng lại và khởi động."
        ;;
    6)
        echo "Thoát."
        exit 0
        ;;
    *)
        echo "Lựa chọn không hợp lệ."
        exit 1
        ;;
esac