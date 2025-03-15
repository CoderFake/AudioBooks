FROM python:3.10-slim

WORKDIR /app

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential git curl unzip wget \
    ffmpeg libsndfile1 python3-dev

# Cài đặt PyTorch phiên bản CPU
RUN pip install torch==2.0.0 torchaudio==2.0.0 torchvision==0.15.1 --index-url https://download.pytorch.org/whl/cpu

# Copy requirements.txt và cài đặt dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Clone F5-TTS từ GitHub
RUN git clone https://github.com/SWivid/F5-TTS.git /opt/F5-TTS
WORKDIR /opt/F5-TTS
RUN pip install -e .

# Tải models Vocos từ HuggingFace
RUN mkdir -p /root/.cache/huggingface
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='charactr/vocos-mel-24khz')"

# Tạo model từ Vocos, tương tự như trong notebook Colab
RUN mkdir -p /opt/models/female

# Tạo file config.json cần thiết cho Vocos
RUN echo '{"decoder": {"type": "vocos", "sampling_rate": 24000, "hop_length": 320}}' > /opt/models/female/config.json

# Thiết lập PYTHONPATH
ENV PYTHONPATH="/opt/F5-TTS/src:/app"

# Quay lại thư mục app
WORKDIR /app

# Copy code ứng dụng
COPY . /app/

# Tạo thư mục cần thiết
RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads

# Expose port
EXPOSE 8000

# Chạy ứng dụng FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]