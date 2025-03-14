import os
import wave
import logging
import subprocess
import tempfile
from typing import List, Optional
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def get_audio_duration(audio_file: str) -> float:

    try:
        if audio_file.lower().endswith('.wav'):
            with wave.open(audio_file, 'r') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        else:
            audio = AudioSegment.from_file(audio_file)
            return len(audio) / 1000.0
    except Exception as e:
        logger.error(f"Error getting audio duration: {str(e)}")
        return 0.0


def concatenate_audio_files(input_files: List[str], output_file: str) -> bool:

    try:
        if not input_files:
            logger.error("No input files provided")
            return False

        output_format = os.path.splitext(output_file)[1].lower().replace('.', '')
        if not output_format:
            output_format = 'wav'

        combined = AudioSegment.from_file(input_files[0])

        for audio_file in input_files[1:]:
            audio_segment = AudioSegment.from_file(audio_file)
            combined += audio_segment

        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        combined.export(output_file, format=output_format)

        return True
    except Exception as e:
        logger.exception(f"Error concatenating audio files: {str(e)}")
        return False


def convert_audio_format(input_file: str, output_file: str, format: str = 'mp3', bitrate: str = '192k') -> bool:
    try:
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format=format, bitrate=bitrate)
        return True
    except Exception as e:
        logger.exception(f"Error converting audio format: {str(e)}")
        return False


def split_audio_file(input_file: str, output_dir: str, segment_duration: int = 60) -> List[str]:
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        audio = AudioSegment.from_file(input_file)

        input_format = os.path.splitext(input_file)[1].lower().replace('.', '')
        if not input_format:
            input_format = 'wav'

        duration_ms = len(audio)
        segment_duration_ms = segment_duration * 1000

        output_files = []

        for i in range(0, duration_ms, segment_duration_ms):
            segment = audio[i:i + segment_duration_ms]
            output_file = os.path.join(output_dir, f"segment_{i // segment_duration_ms}.{input_format}")
            segment.export(output_file, format=input_format)
            output_files.append(output_file)

        return output_files
    except Exception as e:
        logger.exception(f"Error splitting audio file: {str(e)}")
        return []


def normalize_audio(input_file: str, output_file: str = None, target_dBFS: float = -20.0) -> bool:
    try:
        if not output_file:
            output_file = input_file

        audio = AudioSegment.from_file(input_file)

        output_format = os.path.splitext(output_file)[1].lower().replace('.', '')
        if not output_format:
            output_format = 'wav'

        change_in_dBFS = target_dBFS - audio.dBFS

        normalized_audio = audio.apply_gain(change_in_dBFS)

        normalized_audio.export(output_file, format=output_format)

        return True
    except Exception as e:
        logger.exception(f"Error normalizing audio: {str(e)}")
        return False


def add_silence(input_file: str, output_file: str, start_silence_ms: int = 500, end_silence_ms: int = 500) -> bool:
    try:
        audio = AudioSegment.from_file(input_file)

        output_format = os.path.splitext(output_file)[1].lower().replace('.', '')
        if not output_format:
            output_format = 'wav'

        start_silence = AudioSegment.silent(duration=start_silence_ms)
        end_silence = AudioSegment.silent(duration=end_silence_ms)

        padded_audio = start_silence + audio + end_silence

        padded_audio.export(output_file, format=output_format)

        return True
    except Exception as e:
        logger.exception(f"Error adding silence: {str(e)}")
        return False


def optimize_audio_for_streaming(input_file: str, output_file: str) -> bool:
    try:
        output_format = os.path.splitext(output_file)[1].lower().replace('.', '')
        if not output_format:
            output_format = 'mp3'

        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:a'
        ]

        if output_format == 'mp3':
            # Tối ưu MP3 cho streaming
            cmd.extend([
                'libmp3lame',
                '-b:a', '128k',  # Bitrate thấp hơn cho streaming
                '-ac', '1',  # Mono
                '-metadata', 'title=Speech',
                '-f', 'mp3'
            ])
        elif output_format == 'aac' or output_format == 'm4a':
            cmd.extend([
                'aac',
                '-b:a', '96k',  # Bitrate thấp hơn cho streaming
                '-ac', '1',  # Mono
                '-f', 'adts'
            ])
        else:
            cmd.extend([
                'copy'
            ])

        cmd.append(output_file)

        subprocess.run(cmd, check=True)

        return True
    except Exception as e:
        logger.exception(f"Error optimizing audio for streaming: {str(e)}")
        return False


def extract_audio_features(audio_file: str) -> dict:
    try:
        audio = AudioSegment.from_file(audio_file)

        duration_seconds = len(audio) / 1000.0
        channels = audio.channels
        frame_rate = audio.frame_rate
        sample_width = audio.sample_width

        max_amplitude = float(audio.max)

        dBFS = audio.dBFS

        features = {
            "duration": duration_seconds,
            "channels": channels,
            "frame_rate": frame_rate,
            "sample_width": sample_width,
            "max_amplitude": max_amplitude,
            "dBFS": dBFS,
            "format": os.path.splitext(audio_file)[1].lower().replace('.', '')
        }

        return features
    except Exception as e:
        logger.exception(f"Error extracting audio features: {str(e)}")
        return {}