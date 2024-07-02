import subprocess

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from rich import print as rprint
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn
from typing_extensions import Self

from avtools.models import ICommandHandler
from avtools.utils import (
    FilePath,
    check_ffmpeg_installed,
    flatten_list,
    is_supported_extension,
    list_extensions,
)


# region Constants

SUPPORTED_INPUT_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]
SUPPORTED_OUTPUT_EXTENSIONS = [".mp3", ".wav"]

# endregion


# region Parameters


class _CommandParams(BaseModel):
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


# endregion


# region Command


class _VideoToAudioCommand:
    """Convert video to audio."""

    def __init__(self, params: _CommandParams):
        self.params = params

    def execute(self) -> None:
        check_ffmpeg_installed()

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="yellow1", pulse_style="white"),
            TimeElapsedColumn(),
        ) as progress:
            media_conversion_task = progress.add_task(
                "[yellow]Converting video to audio...", total=None
            )
            self._convert_video_to_audio()
            progress.update(
                media_conversion_task,
                description="[green]Video converted to audio[/green]",
            )

    def _convert_video_to_audio(self):
        """Convert video to audio using ffmpeg."""
        command_args = flatten_list(
            [
                ("-i", str(self.params.input_file_path.full_path)),  # Input file
                "-vn",  # No video
                ("-ar", str(self.params.sample_rate)),  # Audio rate
                ("-ab", self.params.bit_rate),  # Audio bitrate
                ("-ac", "1"),  # Audio channels
                # Overwrite output file without asking for confirmation (if it exists)
                "-y",
                str(self.params.output_file_path.full_path),  # Output file
            ]
        )
        output = subprocess.run(["ffmpeg", *command_args], capture_output=True)

        if self.params.verbose:
            rprint(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))
        if output.returncode != 0:
            raise Exception(
                "Error converting video to audio. Enable verbose mode for more information."
            )


# endregion


# region Handler


class VideoToAudioCommandHandler(ICommandHandler):
    def __init__(self):
        self.name = "video-audio"
        self.description = "Convert video to audio."

    def configure_args(self, parser):
        parser.add_argument(
            "-i", "--input_file", required=True, type=str, help="Input video file path"
        )
        parser.add_argument(
            "-o",
            "--output_file",
            default="output.mp3",
            type=str,
            help="Output audio file path. If output file exists, it will be overwritten.",
        )
        parser.add_argument("--verbose", action="store_true", help="Print ffmpeg output")

    def run(self, args) -> None:
        command_params = _CommandParams(
            input_file=args.input_file, output_file=args.output_file, verbose=args.verbose
        )
        _VideoToAudioCommand(command_params).execute()
        rprint(f"[bold green]Audio saved to '{command_params.output_file_path}'[/bold green]")


# endregion
