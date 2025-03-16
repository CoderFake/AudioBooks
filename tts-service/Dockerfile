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

# Tạo thư mục cần thiết
RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads /opt/viet-tts

# Tải VietTTS từ Hugging Face (chỉ clone, không cài đặt)
RUN git clone https://huggingface.co/dangvansam/viet-tts /opt/viet-tts

# Tải models
RUN mkdir -p ~/.config/vietTTS \
    && if [ -d "/opt/viet-tts/models" ]; then cp -r /opt/viet-tts/models/* ~/.config/vietTTS/ || echo "No models to copy"; fi

# Copy code ứng dụng
COPY . /app/

# Expose port
EXPOSE 8000

# Thiết lập PYTHONPATH để tìm thấy cả vietTTS từ models HuggingFace
ENV PYTHONPATH="/app:/opt/viet-tts:${PYTHONPATH}"

# Chạy ứng dụng FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]