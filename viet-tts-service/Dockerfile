FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    libsndfile1 \
    python3-dev \
    curl

RUN mkdir -p /tmp/viet_tts_output

RUN git clone https://github.com/dangvansam/viet-tts.git /opt/viet-tts

RUN pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu

RUN pip install flatbuffers numpy packaging protobuf sympy

RUN pip install --pre --index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/ORT-Nightly/pypi/simple/ onnxruntime

WORKDIR /opt/viet-tts
RUN pip install onnxruntime

RUN pip install -e .

RUN pip install fastapi uvicorn pydantic python-multipart

WORKDIR /app
COPY app.py /app/

ENV PYTHONPATH="/app:/opt/viet-tts:${PYTHONPATH}"

EXPOSE 5000

# Chạy API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]