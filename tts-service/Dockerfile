FROM python:3.10-slim

WORKDIR /app

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential git curl unzip wget \
    ffmpeg libsndfile1 python3-dev

# Cài đặt PyTorch phiên bản CPU
RUN pip install torch==2.0.0 torchaudio==2.0.0 torchvision==0.15.1 --index-url https://download.pytorch.org/whl/cpu

# Tạo thư mục cần thiết
RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads /opt/viet-tts /root/.config/vietTTS

# Clone VietTTS từ GitHub repo gốc
RUN git clone https://github.com/NTT123/vietTTS.git /opt/viet-tts

# Cài đặt VietTTS
RUN cd /opt/viet-tts && pip install -e .

# Tải lexicon.pkl từ releases
RUN curl -L -o /root/.config/vietTTS/lexicon.pkl https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl

# Tạo thư mục cho mô hình và tải mô hình
RUN mkdir -p /root/.config/vietTTS/infore_female
RUN curl -L https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz | tar xz -C /root/.config/vietTTS/infore_female

# Copy code ứng dụng
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

# Expose port
EXPOSE 8000

# Thiết lập PYTHONPATH để tìm thấy VietTTS
ENV PYTHONPATH="/app:/opt/viet-tts:${PYTHONPATH}"

# Chạy ứng dụng FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]