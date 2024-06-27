from typing import Literal
from pydantic import BaseModel

# region Pipelines


class TranscriptionPipelineParams(BaseModel):
    input_file: str
    device_id: str
    model: str = "openai/whisper-large-v3"
    task: Literal["transcribe", "translate"] = "transcribe"
    language: str | None = "es"  # Whisper auto-detects language when set to None
    batch_size: int = 24  # Reduce if running out of memory
    enable_timestamps: bool = False


class DiarizationPipelineParams(BaseModel):
    input_file: str
    hf_token: str
    device_id: str
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    num_speakers: int | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None


# endregion


class CLIArgs(BaseModel):
    input: str
    output: str
    hf_token: str | None = None
