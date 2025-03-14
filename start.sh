
function Handle-Error {
    param (
        [string]$ErrorMessage
    )
    Write-Host "Lỗi: $ErrorMessage" -ForegroundColor Red
    if (-not $isVSCode) {
        Read-Host "Nhấn Enter để thoát..."
    }
    exit 1
}

$isVSCode = $env:TERM_PROGRAM -eq "vscode" -or $env:TERM_PROGRAM -like "*Microsoft*" -or $env:TERM_PROGRAM -like "*VSCode*"

function Create-Directories {
    Write-Host "Tạo các thư mục cần thiết..." -ForegroundColor Cyan
    try {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
        New-Item -ItemType Directory -Path "temp\tts_temp" -Force | Out-Null
        New-Item -ItemType Directory -Path "temp\tts_uploads" -Force | Out-Null
    }
    catch {
        Handle-Error "Không thể tạo thư mục: $_"
    }
    Write-Host "Đã tạo thư mục thành công." -ForegroundColor Green
}

function Check-Docker {
    Write-Host "Kiểm tra Docker..." -ForegroundColor Cyan
    try {
        $null = shell --version
        $null = shell-compose --version
    }
    catch {
        Handle-Error "Docker hoặc Docker Compose chưa được cài đặt. Vui lòng cài đặt trước khi tiếp tục."
    }
    Write-Host "Docker đã được cài đặt." -ForegroundColor Green
}

function Check-EnvFile {
    Write-Host "Kiểm tra file .env..." -ForegroundColor Cyan
    if (-not (Test-Path ".env")) {
        Write-Host "File .env không tồn tại. Đang tạo file từ mẫu..." -ForegroundColor Yellow

        if (Test-Path ".env.example") {
            Copy-Item ".env.example" -Destination ".env"
            Write-Host "Đã tạo file .env từ .env.example" -ForegroundColor Green
        }
        else {
            Write-Host "Không tìm thấy file .env.example, đang tạo file .env mới." -ForegroundColor Yellow

            $jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
            $otpSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
            $ttsSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

            $envContent = @"
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
            JWT_SECRET=$jwtSecret
            JWT_EXPIRES_IN=30d
            EMAIL_NAME=your_email@gmail.com
            EMAIL_PASS=your_email_app_password
            OTP_SECRET=$otpSecret

            # TTS Service Configuration
            TTS_PORT=8000
            DEBUG=True
            PROJECT_NAME=TTS Service
            TTS_SECRET_KEY=$ttsSecret
            DEFAULT_VOICE_MODEL=female
            CHUNK_SIZE=5000

            # Firebase Configuration
            FIREBASE_PROJECT_ID=your-firebase-project-id
            FIREBASE_PRIVATE_KEY=your-firebase-private-key
            FIREBASE_CLIENT_EMAIL=your-firebase-client-email
            FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
            "@
            $envContent | Out-File -FilePath ".env" -Encoding utf8
            Write-Host "Đã tạo file .env mới với các giá trị mặc định và khóa ngẫu nhiên" -ForegroundColor Green
        }

        Write-Host "Vui lòng chỉnh sửa file .env để phù hợp với cấu hình của bạn." -ForegroundColor Yellow
        Write-Host "Nhấn Enter để tiếp tục hoặc Ctrl+C để thoát và chỉnh sửa file .env..." -ForegroundColor Yellow
        Read-Host
    }
    else {
        Write-Host "File .env đã tồn tại." -ForegroundColor Green
    }
}

function Start-Services {
    Write-Host "Đang khởi động các dịch vụ..." -ForegroundColor Cyan
    try {
        $composeFile = if (Test-Path ".\docker-compose.yml") { ".\docker-compose.yml" } else { "docker-compose.yml" }
        shell-compose -f $composeFile up -d
        if ($LASTEXITCODE -ne 0) {
            Handle-Error "Không thể khởi động dịch vụ. Kiểm tra logs để biết thêm chi tiết."
        }
    }
    catch {
        Handle-Error "Lỗi khi khởi động dịch vụ: $_"
    }

    $envVars = @{}
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
                $envVars[$matches[1].Trim()] = $matches[2].Trim()
            }
        }
    }

    $backendPort = if ($envVars.ContainsKey("BACKEND_PORT")) { $envVars["BACKEND_PORT"] } else { "3000" }
    $ttsPort = if ($envVars.ContainsKey("TTS_PORT")) { $envVars["TTS_PORT"] } else { "8000" }
    $mongoExpressPort = if ($envVars.ContainsKey("MONGO_EXPRESS_PORT")) { $envVars["MONGO_EXPRESS_PORT"] } else { "8081" }

    Write-Host "Tất cả dịch vụ đã được khởi động thành công." -ForegroundColor Green
    Write-Host "Backend API: http://localhost:$backendPort" -ForegroundColor Cyan
    Write-Host "TTS Service API: http://localhost:$ttsPort" -ForegroundColor Cyan
    Write-Host "MongoDB Admin UI: http://localhost:$mongoExpressPort" -ForegroundColor Cyan
}

function Stop-Services {
    Write-Host "Đang dừng các dịch vụ..." -ForegroundColor Cyan
    try {
        shell-compose down
        if ($LASTEXITCODE -ne 0) {
            Handle-Error "Không thể dừng dịch vụ. Kiểm tra logs để biết thêm chi tiết."
        }
    }
    catch {
        Handle-Error "Lỗi khi dừng dịch vụ: $_"
    }
    Write-Host "Tất cả dịch vụ đã được dừng thành công." -ForegroundColor Green
}

function Restart-Services {
    Write-Host "Đang khởi động lại các dịch vụ..." -ForegroundColor Cyan
    try {
        shell-compose restart
        if ($LASTEXITCODE -ne 0) {
            Handle-Error "Không thể khởi động lại dịch vụ. Kiểm tra logs để biết thêm chi tiết."
        }
    }
    catch {
        Handle-Error "Lỗi khi khởi động lại dịch vụ: $_"
    }
    Write-Host "Tất cả dịch vụ đã được khởi động lại thành công." -ForegroundColor Green
}


function Show-Logs {
    Write-Host "Đang hiển thị logs (Ctrl+C để thoát)..." -ForegroundColor Cyan
    try {
        shell-compose logs -f
    }
    catch {
        Write-Host "Đã thoát khỏi logs." -ForegroundColor Yellow
    }
}

function Reset-AllData {
    Write-Host "CẢNH BÁO: Thao tác này sẽ xóa tất cả dữ liệu Docker hiện có của dự án!" -ForegroundColor Red
    $confirmation = Read-Host "Bạn có chắc chắn muốn tiếp tục? (y/n)"

    if ($confirmation -eq "y" -or $confirmation -eq "Y") {
        Write-Host "Đang xóa dữ liệu và containers..." -ForegroundColor Yellow
        try {
            shell-compose down -v
            if ($LASTEXITCODE -ne 0) {
                Handle-Error "Không thể xóa dữ liệu. Kiểm tra logs để biết thêm chi tiết."
            }

            Write-Host "Khởi động lại dịch vụ..." -ForegroundColor Cyan
            shell-compose up -d
            if ($LASTEXITCODE -ne 0) {
                Handle-Error "Không thể khởi động lại dịch vụ. Kiểm tra logs để biết thêm chi tiết."
            }

            Write-Host "Dữ liệu đã được xóa và dịch vụ đã được khởi động lại với dữ liệu mới." -ForegroundColor Green
        }
        catch {
            Handle-Error "Lỗi khi xóa dữ liệu: $_"
        }
    }
    else {
        Write-Host "Đã hủy thao tác." -ForegroundColor Yellow
    }
}

function Rebuild-Services {
    Write-Host "Đang xây dựng lại containers..." -ForegroundColor Cyan
    try {
        shell-compose down
        shell-compose build --no-cache
        shell-compose up -d
        if ($LASTEXITCODE -ne 0) {
            Handle-Error "Không thể xây dựng lại containers. Kiểm tra logs để biết thêm chi tiết."
        }
    }
    catch {
        Handle-Error "Lỗi khi xây dựng lại containers: $_"
    }
    Write-Host "Containers đã được xây dựng lại và khởi động." -ForegroundColor Green
}

function Switch-Environment {
    if (Test-Path "docker-compose.prod.yml") {
        Write-Host "Chọn môi trường:" -ForegroundColor Cyan
        Write-Host "1. Development" -ForegroundColor White
        Write-Host "2. Production" -ForegroundColor White
        $envChoice = Read-Host "Lựa chọn"

        if ($envChoice -eq "1") {
            $env:COMPOSE_FILE = "docker-compose.yml"
            Write-Host "Đã chuyển sang môi trường Development." -ForegroundColor Green
        }
        elseif ($envChoice -eq "2") {
            $env:COMPOSE_FILE = "docker-compose.prod.yml"
            Write-Host "Đã chuyển sang môi trường Production." -ForegroundColor Green
        }
        else {
            Write-Host "Lựa chọn không hợp lệ." -ForegroundColor Red
        }
    }
    else {
        Write-Host "File docker-compose.prod.yml không tồn tại. Chỉ có thể sử dụng môi trường Development." -ForegroundColor Yellow
    }
}


function Show-Menu {
    Clear-Host
    Write-Host "=== AudioBooks Management ===" -ForegroundColor Cyan
    Write-Host "1. Khởi động tất cả dịch vụ" -ForegroundColor White
    Write-Host "2. Dừng tất cả dịch vụ" -ForegroundColor White
    Write-Host "3. Khởi động lại tất cả dịch vụ" -ForegroundColor White
    Write-Host "4. Xem logs" -ForegroundColor White
    Write-Host "5. Xóa tất cả dữ liệu và khởi động lại (cẩn thận!)" -ForegroundColor White
    Write-Host "6. Xây dựng lại containers" -ForegroundColor White
    Write-Host "7. Chuyển đổi môi trường" -ForegroundColor White
    Write-Host "8. Thoát" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "Nhập lựa chọn của bạn (1-8)"

    switch ($choice) {
        "1" {
            Start-Services
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "2" {
            Stop-Services
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "3" {
            Restart-Services
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "4" {
            Show-Logs
            Show-Menu
        }
        "5" {
            Reset-AllData
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "6" {
            Rebuild-Services
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "7" {
            Switch-Environment
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
        "8" {
            Write-Host "Thoát." -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "Lựa chọn không hợp lệ." -ForegroundColor Red
            Read-Host "Nhấn Enter để tiếp tục..."
            Show-Menu
        }
    }
}

function Main {
    Check-Docker
    Create-Directories
    Check-EnvFile

    Show-Menu
}

Main