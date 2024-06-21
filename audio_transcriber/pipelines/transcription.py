import torch
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn

from audio_transcriber.models import TranscriptionPipelineParams


def run(config: TranscriptionPipelineParams):
    pipe = pipeline(
        "automatic-speech-recognition",
        model=config.model,
        torch_dtype=torch.float16,
        device=config.device_id,
        model_kwargs={"attn_implementation": "flash_attention_2"} if is_flash_attn_2_available() else {"attn_implementation": "sdpa"},
    )

    if config.device_id == "mps":
        torch.mps.empty_cache()

    generate_kwargs = {
        "task": config.task,
        "language": config.language,
    }

    with Progress(
        TextColumn("🤗 [progress.description]{task.description}"),
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
