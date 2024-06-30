from typing import Literal
from pydantic import BaseModel
import torch
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn, SpinnerColumn


class PipelineParams(BaseModel):
    input_file: str
    device_id: str
    model: str = "openai/whisper-large-v3"
    task: Literal["transcribe", "translate"] = "transcribe"
    language: str | None = None  # Whisper auto-detects language when set to None
    batch_size: int = 24  # Reduce if running out of memory
    enable_timestamps: bool = False


def run(config: PipelineParams):
    pipe = pipeline(
        "automatic-speech-recognition",
        model=config.model,
        torch_dtype=torch.float16,
        device=config.device_id,
        model_kwargs={"attn_implementation": "flash_attention_2"}
        if is_flash_attn_2_available()
        else {"attn_implementation": "sdpa"},
    )

    if config.device_id == "mps":
        torch.mps.empty_cache()

    generate_kwargs = {
        "task": config.task,
        "language": config.language,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(style="yellow1", pulse_style="white"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("[yellow]Transcribing...", total=None)

        outputs = pipe(
            config.input_file,
            chunk_length_s=30,
            batch_size=config.batch_size,
            generate_kwargs=generate_kwargs,
            return_timestamps=config.enable_timestamps,
        )
    return outputs
