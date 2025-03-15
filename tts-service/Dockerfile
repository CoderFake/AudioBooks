FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsndfile1 \
    python3-dev \
    git \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first for better layer caching
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install numpy pydub librosa scipy

# Install F5-TTS using pip (simpler method)
RUN pip install f5-tts

# Download F5-TTS models
RUN mkdir -p ~/.config/f5-tts/models \
    && cd ~/.config/f5-tts/models \
    && curl -L -o female.zip https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/female.zip \
    && curl -L -o male.zip https://github.com/SWivid/F5-TTS/releases/download/v1.0.0/male.zip \
    && unzip -o female.zip \
    && unzip -o male.zip \
    && rm *.zip

# Install VietTTS from GitHub
RUN git clone https://github.com/NTT123/vietTTS.git /opt/vietTTS \
    && cd /opt/vietTTS \
    && pip3 install -e .

# Download VietTTS models
RUN mkdir -p ~/.config/vietTTS \
    && cd ~/.config/vietTTS \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/lexicon.pkl \
    && curl -O https://github.com/NTT123/vietTTS/releases/download/v0.2.0/infore_female_latest.tar.gz \
    && tar -xf infore_female_latest.tar.gz \
    && rm *.tar.gz

ENV PYTHONPATH="${PYTHONPATH}:/opt/vietTTS"
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy application files
COPY . /app/

# Create necessary directories
RUN mkdir -p /tmp/tts_temp /tmp/tts_uploads

# Create fallback provider as a backup
RUN mkdir -p /app/services/tts
COPY services/tts/fallback_provider.py /app/services/tts/
COPY services/tts/tts_base.py /app/services/tts/
COPY services/tts/F5TTS_provider.py /app/services/tts/
COPY services/tts/vietTTS_provider.py /app/services/tts/
COPY services/tts/tts_factory.py /app/services/tts/

# Make sure __init__.py files exist
RUN touch /app/services/__init__.py /app/services/tts/__init__.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]