FROM python:3.10-slim

WORKDIR /app

# Thêm các thư viện cần thiết cho TTS và audio processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    portaudio19-dev \
    python3-dev \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các gói Python cần thiết
COPY requirements.txt /app/
RUN pip install "pip<24.1"
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt VietTTS từ GitHub
RUN git clone https://github.com/NTT123/vietTTS.git /vietTTS \
    && cd /vietTTS \
    && pip install -e .

# Tải models cho VietTTS
RUN mkdir -p /root/.config/vietTTS \
    && cd /root/.config/vietTTS \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_male_latest.tar.gz \
    && tar -xf infore_female_latest.tar.gz \
    && tar -xf infore_male_latest.tar.gz \
    && rm *.tar.gz

# Tạo thư mục lưu trữ tạm thời
RUN mkdir -p /tmp/tts_temp

# Sao chép mã nguồn ứng dụng
COPY . /app/

# Expose cổng API
EXPOSE 8000

# Khởi chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]