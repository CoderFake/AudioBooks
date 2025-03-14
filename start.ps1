
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Cảnh báo: Script này không chạy với quyền sudo. Một số thao tác có thể thất bại."
        echo "Bạn có muốn tiếp tục không? (y/n)"
        read -r choice
        if [[ $choice != "y" && $choice != "Y" ]]; then
            echo "Đã hủy."
            exit 1
        fi
    fi
}

handle_error() {
    echo "Lỗi: $1"
    exit 1
}

check_requirements() {

    if ! command -v docker &> /dev/null; then
        handle_error "Docker chưa được cài đặt. Vui lòng cài đặt Docker và Docker Compose."
    fi

    if ! command -v docker-compose &> /dev/null; then
        handle_error "Docker Compose chưa được cài đặt. Vui lòng cài đặt Docker Compose."
    fi
}

create_directories() {
    echo "Tạo các thư mục cần thiết..."
    mkdir -p logs temp/tts_temp temp/tts_uploads || handle_error "Không thể tạo thư mục"
    chmod -R 777 logs temp/tts_temp temp/tts_uploads || handle_error "Không thể cấp quyền cho thư mục"
}


check_env_file() {
    if [ ! -f .env ]; then
        echo "File .env không tồn tại. Tạo file từ mẫu..."
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "Đã tạo file .env từ .env.example"
        else
            cat > .env << EOL

HOST_NAME=localhost
EXTERNAL_HOST=0.0.0.0

MONGO_USERNAME=admin
MONGO_PASSWORD=123456
MONGO_DATABASE=audiobooksDB
MONGO_PORT=27017
MONGO_EXPRESS_PORT=8081
MONGO_EXPRESS_USER=user
MONGO_EXPRESS_PASSWORD=password

BACKEND_PORT=3000
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRES_IN=30d
EMAIL_NAME=your_email@gmail.com
EMAIL_PASS=your_email_app_password
OTP_SECRET=$(openssl rand -hex 16)

TTS_PORT=8000
DEBUG=True
PROJECT_NAME=TTS Service
TTS_SECRET_KEY=$(openssl rand -hex 32)
DEFAULT_VOICE_MODEL=female
CHUNK_SIZE=5000

FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email
FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
EOL
    echo "Đã tạo file .env mới với các giá trị mặc định và khóa ngẫu nhiên"
    fi
        echo "Vui lòng chỉnh sửa file .env để phù hợp với cấu hình của bạn."
        echo "Nhấn Enter để tiếp tục hoặc Ctrl+C để thoát và chỉnh sửa file .env..."
        read -r
    fi
}

start_services() {
    echo "Đang khởi động các dịch vụ..."
    docker-compose up -d
    if [ $? -ne 0 ]; then
        handle_error "Không thể khởi động dịch vụ. Kiểm tra logs để biết thêm chi tiết."
    fi
    echo "Tất cả dịch vụ đã được khởi động thành công."
    echo "Backend API: http://localhost:${BACKEND_PORT:-3000}"
    echo "TTS Service API: http://localhost:${TTS_PORT:-8000}"
    echo "MongoDB Admin UI: http://localhost:${MONGO_EXPRESS_PORT:-8081}"
}

stop_services() {
    echo "Đang dừng các dịch vụ..."
    docker-compose down
    if [ $? -ne 0 ]; then
        handle_error "Không thể dừng dịch vụ. Kiểm tra logs để biết thêm chi tiết."
    fi
    echo "Tất cả dịch vụ đã được dừng thành công."
}

restart_services() {
    echo "Đang khởi động lại các dịch vụ..."
    docker-compose restart
    if [ $? -ne 0 ]; then
        handle_error "Không thể khởi động lại dịch vụ. Kiểm tra logs để biết thêm chi tiết."
    fi
    echo "Tất cả dịch vụ đã được khởi động lại thành công."
}

show_logs() {
    echo "Đang hiển thị logs (Ctrl+C để thoát)..."
    docker-compose logs -f
}

reset_data() {
    echo "CẢNH BÁO: Thao tác này sẽ xóa tất cả dữ liệu và containers!"
    echo "Bạn có chắc chắn muốn tiếp tục? (y/n)"
    read -r confirmation
    if [[ $confirmation == "y" || $confirmation == "Y" ]]; then
        echo "Đang xóa dữ liệu và containers..."
        docker-compose down -v
        if [ $? -ne 0 ]; then
            handle_error "Không thể xóa dữ liệu. Kiểm tra logs để biết thêm chi tiết."
        fi
        echo "Đã xóa toàn bộ dữ liệu."
        
        echo "Khởi động lại dịch vụ..."
        docker-compose up -d
        if [ $? -ne 0 ]; then
            handle_error "Không thể khởi động lại dịch vụ. Kiểm tra logs để biết thêm chi tiết."
        fi
        echo "Dịch vụ đã được khởi động lại với dữ liệu mới."
    else
        echo "Đã hủy thao tác."
    fi
}

rebuild_services() {
    echo "Đang xây dựng lại containers..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    if [ $? -ne 0 ]; then
        handle_error "Không thể xây dựng lại containers. Kiểm tra logs để biết thêm chi tiết."
    fi
    echo "Containers đã được xây dựng lại và khởi động."
}

switch_environment() {
    if [ -f docker-compose.prod.yml ]; then
        echo "Chọn môi trường:"
        echo "1. Development"
        echo "2. Production"
        read -r env_choice
        
        if [ "$env_choice" == "1" ]; then
            export COMPOSE_FILE=docker-compose.yml
            echo "Đã chuyển sang môi trường Development."
        elif [ "$env_choice" == "2" ]; then
            export COMPOSE_FILE=docker-compose.prod.yml
            echo "Đã chuyển sang môi trường Production."
        else
            echo "Lựa chọn không hợp lệ."
        fi
    else
        echo "File docker-compose.prod.yml không tồn tại. Chỉ có thể sử dụng môi trường Development."
    fi
}

show_menu() {
    echo "=== AudioBooks Services Management ==="
    echo "1. Khởi động dịch vụ"
    echo "2. Dừng dịch vụ"
    echo "3. Khởi động lại dịch vụ"
    echo "4. Xem logs"
    echo "5. Xóa tất cả dữ liệu và khởi động lại (cẩn thận!)"
    echo "6. Xây dựng lại containers"
    echo "7. Chuyển đổi môi trường"
    echo "8. Thoát"
    echo -n "Nhập lựa chọn của bạn (1-8): "
    read -r choice

    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) show_logs ;;
        5) reset_data ;;
        6) rebuild_services ;;
        7) switch_environment ;;
        8) echo "Thoát."; exit 0 ;;
        *) echo "Lựa chọn không hợp lệ." ;;
    esac

    echo ""
    read -p "Nhấn Enter để tiếp tục..."
    show_menu
}