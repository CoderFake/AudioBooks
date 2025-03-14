FROM python:3.10-slim

WORKDIR /app

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

COPY requirements.txt /app/
RUN pip install "pip<24.1"
RUN pip install --no-cache-dir -r requirements.txt

RUN git clone https://github.com/NTT123/vietTTS.git /vietTTS \
    && cd /vietTTS \
    && pip install -e .

RUN mkdir -p /root/.config/vietTTS \
    && cd /root/.config/vietTTS \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_male_latest.tar.gz \
    && tar -xf infore_female_latest.tar.gz \
    && tar -xf infore_male_latest.tar.gz \
    && rm *.tar.gz

RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads

COPY . /app/

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]