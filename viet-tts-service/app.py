import os
import tempfile
import logging
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import uuid
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("viet-tts-service")

app = FastAPI(title="VietTTS API Service")

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="/tmp/viet_tts_output"), name="static")

os.makedirs("/tmp/viet_tts_output", exist_ok=True)


class TTSRequest(BaseModel):
    text: str
    voice: str = "0"
    output_format: str = "wav"
    return_url: bool = False


class Voice(BaseModel):
    id: str
    name: str
    gender: str = "unknown"
    description: str = ""


@app.get("/")
async def root():
    return {"message": "VietTTS API Service", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    try:
        result = subprocess.run(
            ["viettts", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "healthy", "message": "VietTTS CLI is available"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")


@app.get("/voices", response_model=List[Voice])
async def get_voices():
    try:
        result = subprocess.run(
            ["viettts", "show-voices"],
            capture_output=True,
            text=True,
            check=True
        )

        voice_lines = result.stdout.strip().split('\n')
        voices = []

        for line in voice_lines:
            if line.strip():
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    voice_id = parts[0].strip()
                    description = parts[1].strip()
                    gender = "female"
                    if "male" in description.lower():
                        gender = "male"

                    voices.append(Voice(
                        id=voice_id,
                        name=description,
                        gender=gender,
                        description=description
                    ))

        if not voices:
            voices = [
                Voice(id="0", name="Default Female Voice", gender="female",
                      description="Default built-in female voice"),
                Voice(id="1", name="Default Male Voice", gender="male", description="Default built-in male voice"),
            ]

        return voices

    except Exception as e:
        logger.exception(f"Lỗi khi lấy danh sách giọng: {str(e)}")
        return [
            Voice(id="0", name="Default Female Voice", gender="female", description="Default built-in female voice"),
            Voice(id="1", name="Default Male Voice", gender="male", description="Default built-in male voice"),
        ]


@app.post("/synthesize")
async def synthesize_text(request: TTSRequest, background_tasks: BackgroundTasks):
    try:
        output_id = str(uuid.uuid4())
        output_path = f"/tmp/viet_tts_output/{output_id}.{request.output_format}"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as text_file:
            text_file_path = text_file.name
            text_file.write(request.text)

        logger.info(f"Đang tổng hợp văn bản: '{request.text[:50]}...' với giọng {request.voice}")

        cmd = [
            "viettts", "synthesis",
            "--text", request.text,
            "--voice", request.voice,
            "--output", output_path
        ]

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise Exception(f"Error in viettts CLI: {process.stderr}")

        logger.info(f"Đã tạo file âm thanh: {output_path}")

        try:
            os.unlink(text_file_path)
        except:
            pass

        if not request.return_url:
            background_tasks.add_task(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)

        if request.return_url:
            file_name = os.path.basename(output_path)
            return {
                "success": True,
                "message": "Synthesis completed",
                "file_path": output_path,
                "url": f"/static/{file_name}"
            }
        else:
            return FileResponse(
                output_path,
                media_type=f"audio/{request.output_format}",
                filename=f"tts_output_{output_id}.{request.output_format}"
            )

    except Exception as e:
        logger.exception(f"Lỗi khi tổng hợp giọng nói: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clone-voice")
async def clone_voice(
        text: str,
        voice_file: str,
        output_format: str = "wav",
        background_tasks: BackgroundTasks,
        return_url: bool = False
):
    try:
        if not os.path.exists(voice_file):
            raise HTTPException(status_code=404, detail=f"Voice file not found: {voice_file}")

        output_id = str(uuid.uuid4())
        output_path = f"/tmp/viet_tts_output/{output_id}.{output_format}"

        logger.info(f"Đang tổng hợp văn bản với giọng đã clone: '{text[:50]}...'")

        cmd = [
            "viettts", "synthesis",
            "--text", text,
            "--voice", voice_file,
            "--output", output_path
        ]

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise Exception(f"Error in viettts CLI: {process.stderr}")

        logger.info(f"Đã tạo file âm thanh với giọng clone: {output_path}")

        if not return_url:
            background_tasks.add_task(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)

        if return_url:
            file_name = os.path.basename(output_path)
            return {
                "success": True,
                "message": "Voice cloning synthesis completed",
                "file_path": output_path,
                "url": f"/static/{file_name}"
            }
        else:
            return FileResponse(
                output_path,
                media_type=f"audio/{output_format}",
                filename=f"tts_voice_clone_{output_id}.{output_format}"
            )

    except Exception as e:
        logger.exception(f"Lỗi khi tổng hợp giọng nói với giọng đã clone: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)