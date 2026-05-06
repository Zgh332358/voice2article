"""STT 路由：文件上传 → 调 Step ASR → 返回转写文本。"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import CurrentUser
from app.core.errors import AppError
from app.core.logging import get_logger
from app.schemas import TranscribeResponse
from app.services.stt import StepASRClient, get_stt_client

router = APIRouter(prefix="/stt", tags=["stt"])
logger = get_logger(__name__)

# Step ASR 已实测支持的格式 + 浏览器 MediaRecorder 常见输出
ALLOWED_CONTENT_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/x-m4a",
        "audio/aiff",
        "audio/x-aiff",
        "audio/ogg",
        "audio/webm",
        "audio/flac",
    }
)
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB


class FileTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = "file_too_large"


class UnsupportedAudioFormatError(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    code = "unsupported_audio"


class EmptyAudioError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "empty_audio"


SttClientDep = Annotated[StepASRClient, Depends(get_stt_client)]
AudioFile = Annotated[
    UploadFile,
    File(description="音频文件，支持 wav/mp3/m4a/aiff/ogg/webm/flac"),
]


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="语音转写（文件上传）",
)
async def transcribe(
    current_user: CurrentUser,
    stt_client: SttClientDep,
    file: AudioFile,
) -> TranscribeResponse:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedAudioFormatError(f"不支持的音频格式：{file.content_type}")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise EmptyAudioError("音频文件为空")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise FileTooLargeError(f"音频超过 {MAX_AUDIO_BYTES // 1024 // 1024}MB 限制")

    text = await stt_client.transcribe(
        audio=audio_bytes,
        filename=file.filename or "audio.wav",
        content_type=file.content_type or "audio/wav",
    )

    logger.info(
        "user=%s transcribed %d bytes -> %d chars",
        current_user.id,
        len(audio_bytes),
        len(text),
    )
    return TranscribeResponse(text=text, model=stt_client.model, audio_bytes=len(audio_bytes))
