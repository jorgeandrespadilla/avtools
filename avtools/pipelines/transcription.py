from typing import Literal
from pydantic import BaseModel
import torch
from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers.utils import is_flash_attn_2_available
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn, SpinnerColumn

from avtools.utils import resolve_device_type


class PipelineParams(BaseModel):
    input_file: str
    model_id: str = "openai/whisper-large-v3-turbo"
    task: Literal["transcribe", "translate"] = "transcribe"
    device_id: str | None = None
    language: str | None = None  # Whisper auto-detects language when set to None
    batch_size: int = 24  # Reduce if running out of memory
    enable_timestamps: bool = False


def run(config: PipelineParams):
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    device = resolve_device_type(config.device_id)

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        config.model_id, 
        torch_dtype=torch_dtype, 
        low_cpu_mem_usage=True,
        use_safetensors=True,
        attn_implementation="flash_attention_2" if is_flash_attn_2_available() else "sdpa"
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(config.model_id)
    
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        batch_size=config.batch_size, # Batch size for inference (set based on the device's memory)
        torch_dtype=torch_dtype,
        device=device,
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
            generate_kwargs=generate_kwargs,
            return_timestamps=config.enable_timestamps,
        )
    return outputs
