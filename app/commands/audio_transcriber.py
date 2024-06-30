import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from rich import print as rprint
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn, SpinnerColumn

from app.models import ICommandHandler, TranscriptionResultData
from app.utils import FilePath, get_env, is_supported_extension, is_url, list_extensions


# region Constants


SUPPORTED_INPUT_EXTENSIONS = [".mp3", ".wav"]
SUPPORTED_OUTPUT_EXTENSIONS = [".json"]
HUGGING_FACE_TOKEN_ENV_VAR = "HUGGING_FACE_TOKEN"


# endregion


# region Parameters


class _CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_file: str
    """
    Input video file path or URL. 
    If input file is not a URL, do not use this field directly, use the input_file_path property instead.
    """

    output_file: str
    """Output audio file path (do not use this field directly, use the output_file_path property instead)."""

    language: str | None = None
    """Language code to use for transcription."""

    hf_token: str | None = None
    """Hugging Face API token for diarization. If omitted, diarization will be disabled."""

    # Additional parameters
    device_id: str = "cuda:0"
    """
    Device ID to use for processing. Use 'cuda:{#}' for GPU devices or 'mps' for Mac devices.
    """

    enable_timestamps: bool = True
    """Enable timestamps in the transcription output."""

    @computed_field
    @property
    def input_file_or_url(self) -> str:
        """Get the input file path or URL as a string."""
        if is_url(self.input_file):
            return self.input_file
        return str(self.input_file_path)

    @computed_field
    @property
    def input_file_path(self) -> FilePath:
        """Get the input file path (fails if input is a URL)."""
        if is_url(self.input_file):
            raise ValueError("Cannot get file path for URL input (this should not happen).")
        return FilePath(self.input_file)

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)

    @model_validator(mode="after")
    def _validate_files(self) -> Self:
        self._validate_input_file()

        self._validate_output_file()

        if self.hf_token and not self.enable_timestamps:
            raise ValueError("Diarization requires timestamps to be enabled.")
        return self

    def _validate_input_file(self):
        if is_url(self.input_file):
            return self

        if not self.input_file_path.file_exists():
            raise FileNotFoundError(f"File not found: '{self.input_file_path.full_path}'")
        if not is_supported_extension(self.input_file_path.extension, SUPPORTED_INPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid input file format: '{self.input_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
            )
        return self

    def _validate_output_file(self):
        if not self.output_file_path.directory_exists():
            raise FileNotFoundError(
                f"Directory not found: '{self.output_file_path.directory_path}'"
            )
        if not is_supported_extension(self.output_file_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid output file format: '{self.output_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
            )


# endregion


# region Command


class _TranscriberCommand:
    """Transcribe audio files."""

    def __init__(self, params: _CommandParams):
        self.params = params

    def execute(self) -> None:
        # Load AI pipelines
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="yellow1", pulse_style="white"),
            TimeElapsedColumn(),
        ) as progress:
            load_models_task = progress.add_task("[yellow]Loading AI pipelines...", total=None)

            from app.pipelines import transcription, diarization

            progress.update(
                load_models_task,
                description="[green]AI pipelines loaded.",
                completed=1,
                total=1, 
            )

        # Transcription
        transcription_params = transcription.PipelineParams(
            input_file=self.params.input_file_or_url,
            device_id=self.params.device_id,
            enable_timestamps=self.params.enable_timestamps,
            language=self.params.language,
        )
        transcription_result = transcription.run(transcription_params)

        # Diarization
        if self.params.hf_token:
            diarization_params = diarization.PipelineParams(
                input_file=self.params.input_file_or_url,
                device_id=self.params.device_id,
                hf_token=self.params.hf_token,
            )
            diarization_result = diarization.run(
                diarization_params, transcription_result
            )  # Speakers transcript
            result = self._build_result(diarization_result, transcription_result)
        else:
            result = self._build_result([], transcription_result)

        with open(self.params.output_file_path.full_path, "w", encoding="utf8") as fp:
            json.dump(result.model_dump(), fp, ensure_ascii=False)


    def _build_result(self, diarization_chunks: list, outputs) -> TranscriptionResultData:
        """
        Build the final transcription result using the output of the
        diarization and transcription pipelines.
        """
        return TranscriptionResultData(
            speakers=diarization_chunks,
            chunks=outputs["chunks"],
            text=outputs["text"],
        )


# endregion


# region Handler


class TranscriberCommandHandler(ICommandHandler):
    def __init__(self):
        self.name = "transcribe"
        self.description = "Transcribe audio files."

    def configure_args(self, parser):
        parser.add_argument(
            "-i",
            "--input",
            required=True,
            type=str,
            help="Path or URL to the audio file to be transcribed.",
        )
        parser.add_argument(
            "-o",
            "--output",
            required=False,
            default="output.json",
            type=str,
            help=f"Path to save the transcription. If not provided, the output will be saved in the same directory as the input file. Format will be inferred from the file extension. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}.",
        )
        parser.add_argument(
            "--language",
            required=False,
            default=None,
            type=str,
            help="Provide the language code for the audio file (eg. 'en', 'es'). If not provided, the language will be detected automatically. For a list of supported languages, visit https://github.com/openai/whisper#available-models-and-languages.",
        )
        parser.add_argument(
            "--hf-token",
            required=False,
            default=None,
            type=str,
            help=f"Provide a hf.co/settings/token for Pyannote.audio to diarise the audio clips. If not provided, it will be searched in the environment variables ({HUGGING_FACE_TOKEN_ENV_VAR}). If not found, diarization will be skipped. To use this feature, follow the instructions in https://huggingface.co/pyannote/speaker-diarization-3.1.",
        )

    def run(self, args) -> None:
        hf_token = args.hf_token or get_env(HUGGING_FACE_TOKEN_ENV_VAR)

        command_params = _CommandParams(
            input_file=args.input,
            output_file=args.output,
            language=args.language,
            hf_token=hf_token,  # Use diarization model
        )
        _TranscriberCommand(command_params).execute()

        rprint(
            f"[bold green]Transcription saved to '{command_params.output_file_path}'[/bold green]"
        )


# endregion
