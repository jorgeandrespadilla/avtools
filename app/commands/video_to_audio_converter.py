import subprocess

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn
from typing_extensions import Self

from app.utils import (
    FilePath,
    check_ffmpeg_installed,
    flatten_list,
    is_supported_extension,
    list_extensions,
)

SUPPORTED_INPUT_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]
SUPPORTED_OUTPUT_EXTENSIONS = [".mp3", ".wav"]


class CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_file: str
    """Input video file path (do not use this field directly, use the input_file_path property instead)."""

    output_file: str
    """Output audio file path (do not use this field directly, use the output_file_path property instead)."""

    verbose: bool = False
    """Enable verbose mode."""

    # Additional parameters
    sample_rate: int = 44100
    """Audio sample rate."""

    bit_rate: str = "128k"
    """Audio bitrate."""

    @computed_field
    @property
    def input_file_path(self) -> FilePath:
        return FilePath(self.input_file)

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)

    @model_validator(mode="after")
    def _validate_files(self) -> Self:
        input_path = FilePath(self.input_file)
        if not input_path.file_exists():
            raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
        if not is_supported_extension(input_path.extension, SUPPORTED_INPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid input file format: '{input_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
            )

        output_path = FilePath(self.output_file)
        if not output_path.directory_exists():
            raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
        if not is_supported_extension(output_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
            )
        return self


def _build_ffmpeg_args(params: CommandParams) -> list[str]:
    """Generate the arguments for the ffmpeg command to convert video to audio."""

    return flatten_list(
        [
            ("-i", str(params.input_file_path.full_path)),  # Input file
            "-vn",  # No video
            ("-ar", str(params.sample_rate)),  # Audio rate
            ("-ab", params.bit_rate),  # Audio bitrate
            ("-ac", "1"),  # Audio channels
            # Overwrite output file without asking for confirmation (if it exists)
            "-y",
            str(params.output_file_path.full_path),  # Output file
        ]
    )


def execute(params: CommandParams) -> None:
    """Convert video to audio."""

    check_ffmpeg_installed()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(style="yellow1", pulse_style="white"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("[yellow]Converting video to audio...", total=None)

        command_args = _build_ffmpeg_args(params)
        output = subprocess.run(["ffmpeg", *command_args], capture_output=True)

    if params.verbose:
        print(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))
    if output.returncode != 0:
        raise Exception(
            "Error converting video to audio. Enable verbose mode for more information."
        )
