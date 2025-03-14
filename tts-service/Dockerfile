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
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt


RUN git clone https://github.com/SWivid/F5-TTS.git /opt/F5-TTS \
    && cd /opt/F5-TTS \
    && pip install -e .

RUN mkdir -p /root/.config/f5-tts/models \
    && cd /root/.config/f5-tts/models \
    && curl -L -o female.zip https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/female.zip \
    && curl -L -o male.zip https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/male.zip \
    && unzip female.zip \
    && unzip male.zip \
    && rm *.zip

RUN git clone https://github.com/NTT123/vietTTS.git /opt/vietTTS \
    && cd /opt/vietTTS \
    && pip install -e .

RUN mkdir -p /root/.config/vietTTS \
    && cd /root/.config/vietTTS \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz \
    && tar -xf infore_female_latest.tar.gz \
    && rm *.tar.gz

RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads

COPY . /app/

RUN python -c "
import os
print('F5-TTS Models:')
print(os.listdir('/root/.config/f5-tts/models'))
print('\nVietTTS Models:')
print(os.listdir('/root/.config/vietTTS'))
"

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]