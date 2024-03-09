from pydantic import BaseModel


class TranscriptionConfig(BaseModel):
    input_file: str
    device_id: str
    model: str = "openai/whisper-large-v3"
    task: str = "transcribe" # Options: "transcribe", "translate"
    language: str | None = None # Whisper auto-detects language
    batch_size: int = 24 # Reduce if running out of memory
    enable_timestamps: bool = False


class DiarizationConfig(BaseModel):
    input_file: str
    hf_token: str
    device_id: str
    diarization_model: str = 'pyannote/speaker-diarization-3.1'
    num_speakers: int | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None


class CLIArgs(BaseModel):
    input: str
    output: str
    hf_token: str | None = None
