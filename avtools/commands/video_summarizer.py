from pathlib import Path
import subprocess
from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from rich import print as rprint
from rich.progress import (
    Progress,
    TimeElapsedColumn,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    TaskID,
)
from typing_extensions import Self

from avtools.models import ICommandHandler
from avtools.utils import (
    FilePath,
    check_ffmpeg_installed,
    flatten_list,
    get_env,
    is_supported_extension,
    list_extensions,
)


# region Constants

SUPPORTED_INPUT_VIDEO_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]
SUPPORTED_INPUT_TRANSCRIPT_EXTENSIONS = [".vtt"]
OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"

# endregion


# region Parameters


class _CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_video_file: str
    """Path to the video file."""

    input_transcript_file: str
    """Path to the transcript file in VTT format."""

    output_dir: str
    """Output folder path (the files will be saved in this folder). If the folder does not exist, it will be created."""

    openai_key: str
    """OpenAI API key for summarizing the video."""

    verbose: bool = False
    """Enable verbose mode."""

    @computed_field
    @property
    def input_video_file_path(self) -> FilePath:
        return FilePath(self.input_video_file)

    @computed_field
    @property
    def input_transcript_file_path(self) -> FilePath:
        return FilePath(self.input_transcript_file)

    @computed_field
    @property
    def output_dir_path(self) -> Path:
        return Path(self.output_dir)

    @model_validator(mode="after")
    def _validate_fields(self) -> Self:
        if not self.input_video_file_path.file_exists():
            raise FileNotFoundError(f"File not found: '{self.input_video_file_path.full_path}'")
        if not is_supported_extension(
            self.input_video_file_path.extension, SUPPORTED_INPUT_VIDEO_EXTENSIONS
        ):
            raise ValueError(
                f"Invalid input video file format: '{self.input_video_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_VIDEO_EXTENSIONS)}"
            )

        if not self.input_transcript_file_path.file_exists():
            raise FileNotFoundError(
                f"File not found: '{self.input_transcript_file_path.full_path}'"
            )
        if not is_supported_extension(
            self.input_transcript_file_path.extension, SUPPORTED_INPUT_TRANSCRIPT_EXTENSIONS
        ):
            raise ValueError(
                f"Invalid input transcript file format: '{self.input_transcript_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_TRANSCRIPT_EXTENSIONS)}"
            )

        if self.output_dir_path.exists():
            if not self.output_dir_path.is_dir():
                raise NotADirectoryError(
                    f"'{self.output_dir_path}' is not a directory. Please provide a valid directory path."
                )
            if len(list(self.output_dir_path.iterdir())) > 0:
                raise ValueError(
                    f"The output directory '{self.output_dir_path}' is not empty. Please provide another directory or an empty one."
                )
        else:
            if self.verbose:
                rprint(f"Creating output directory: '{self.output_dir_path}'")
            self.output_dir_path.mkdir(parents=True, exist_ok=True)

        return self


class VideoSummaryParams(BaseModel):
    """
    Parameters for the video summary.
    """

    transcript: str
    """Transcript of the video in VTT format."""

    output_summary_file: Path
    """Output file path for the summary (Markdown format)."""

    output_extracts_dir: Path
    """Output folder path for the video extracts."""

    verbose: bool = False
    """Enable verbose mode."""

    @model_validator(mode="after")
    def _validate_fields(self) -> Self:
        if not self.output_summary_file.parent.exists():
            raise FileNotFoundError(
                f"Output directory not found: '{self.output_summary_file.parent}' (this should not happen)."
            )

        if self.output_extracts_dir.exists():
            if not self.output_extracts_dir.is_dir():
                raise NotADirectoryError(
                    f"'{self.output_extracts_dir}' is not a directory. Please provide a valid directory path (this should not happen)."
                )
        else:
            if self.verbose:
                rprint(f"Creating extracts output directory: '{self.output_extracts_dir}'")
            self.output_extracts_dir.mkdir(parents=True, exist_ok=True)

        return self


# endregion


# region Data Classes


class VideoSummaryExtractData:
    """
    Data class to manage the video summary extracts.
    """

    def __init__(self, title: str, start_time: str, end_time: str, video_extract_path: FilePath):
        self.title = title
        """Title of the extract."""

        self.start_time = start_time
        """Start time of the extract."""

        self.end_time = end_time
        """End time of the extract."""

        self.video_extract_path = video_extract_path
        """Path to the video extract file."""

    def __str__(self) -> str:
        return f"{self.title} ({self.start_time} - {self.end_time})"


class VideoSummarySectionData:
    """
    Data class to manage the video summary sections.
    """

    def __init__(
        self,
        title: str,
        content: str,
        start_time: str,
        end_time: str,
        extracts: list[VideoSummaryExtractData] = [],
    ):
        self.title = title
        """Title of the section."""

        self.content = content
        """Content of the section."""

        self.start_time = start_time
        """Start time of the section."""

        self.end_time = end_time
        """End time of the section."""

        self.extracts = extracts
        """List of extracts with the most important parts of the video."""

    def add_extract(self, extract: VideoSummaryExtractData) -> None:
        """
        Add an extract to the section.
        """
        self.extracts.append(extract)

    def __str__(self) -> str:
        return f"{self.title} ({self.start_time} - {self.end_time})"


class VideoSummaryData:
    """
    Data class to manage the video summary data.
    """

    def __init__(
        self,
        title: str,
        summary: str = "",
        sections: list[VideoSummarySectionData] = [],
    ):
        self.title = title
        """Title of the video."""

        self.summary = summary
        """TL;DR summary of the video."""

        self.sections = sections
        """List of sections with the most important topics of the video and the corresponding timestamps."""

    def add_section(self, section: VideoSummarySectionData) -> None:
        """
        Add a section to the video summary.
        """
        self.sections.append(section)

    def __str__(self) -> str:
        return f"{self.title} ({len(self.sections)} sections)"


# endregion


# region Utilities


class MarkdownSummaryFormatter:
    """
    Formatter to generate a Markdown summary of the video.
    """

    @staticmethod
    def format_summary(data: VideoSummaryData, output_dir_path: Path) -> str:
        """
        Format the video summary data as a Markdown document.

        Parameters:
        - data: VideoSummaryData - Video summary data.
        - output_dir_path: Path - Output directory path where the summary will be saved. This path will be used to resolve the paths of the video extracts in the Markdown document.
        """

        summary = f"# {data.title}\n\n"
        summary += f"{data.summary}\n\n"

        for section in data.sections:
            summary += f"## {section.title}\n\n"
            summary += f"{section.content}\n\n"

            for extract in section.extracts:
                summary += f"### {extract.title}\n\n"
                summary += f"Start time: {extract.start_time} - End time: {extract.end_time}\n\n"
                relative_extract_path = extract.video_extract_path.full_path.relative_to(
                    output_dir_path
                )
                summary += f"![Extract](./{relative_extract_path})\n\n"

        return summary


# endregion


# region Command


class _SummarizeCommand:
    """
    Summarize a video by taking its transcript (required) and generating a detailed summary.
    It can also include extracts from the most important parts of the video.

    Remarks
    ----
    - If the output folder does not exist, it will be created.
    """

    """
    Command input:
    - Path to the video file.
    - Path to the transcript file in VTT format.
    - Output folder path (the files will be saved in this folder).
    
    Steps to summarize the video:
    1. Load the transcript file.
    3. Generate a TL;DR summary of the video based on the transcript.
    2. Generate a detailed summary of the video based on the transcript, defining a list of sections with the  most important topics of the video and the corresponding timestamps.
        2.1. For each section, generate a summary based on the transcript.
        2.2. For each section, define a list of the start and end timestamps of the most important extracts of the video, trying to be concise and informative. Also include a short and clear title that describes the content of the extract (the amount of extracts should be proportional to the richness of the content).
        2.3. Extract the video segments corresponding to the most important parts of the video and save them in the output folder (with the format: 'part-{number}_extract-{number}.mp4') using ffmpeg.
    4. Save the TL;DR summary and the detailed summary in the output folder. For each section, save the summary and the list of extracts with the corresponding timestamps.
    """

    def __init__(self, params: _CommandParams):
        self.params = params
        self.summary_params = VideoSummaryParams(
            transcript=self._load_transcript(),
            output_summary_file=self.params.output_dir_path / "summary.md",
            output_extracts_dir=self.params.output_dir_path / "video_extracts",
            verbose=self.params.verbose,
        )
        self.summary = VideoSummaryData(title="Video Summary")

    def execute(self) -> None:
        """
        Execute the command.
        """

        check_ffmpeg_installed()

        self._extract_video_segment("00:00:00", "00:00:10", "output.mp4")

    def _load_transcript(self) -> str:
        """
        Load the transcript file.
        """
        with open(self.params.input_transcript_file_path.full_path, "r", encoding="utf-8") as f:
            transcript = f.read()
        return transcript

    def _extract_video_segment(self, start_time: str, end_time: str, output_file: str) -> None:
        """
        Extract a video segment using ffmpeg.
        """
        # ffmpeg -i input.mp4 -ss 00:00:10 -to 00:00:20 -c copy output.mp4

        command_args = flatten_list(
            [
                ("-i", self.params.input_video_file_path.full_path),  # Input video file
                ("-ss", start_time),  # Start time
                ("-to", end_time),  # End time
                ("-c", "copy"),  # Copy the video and audio streams
                "-y",  # Overwrite output file without asking for confirmation (if it exists)
                str(self.summary_params.output_extracts_dir / output_file),  # Output file
            ]
        )
        output = subprocess.run(["ffmpeg", *command_args], capture_output=True)

        if self.params.verbose:
            rprint(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))
        if output.returncode != 0:
            raise Exception(
                "An error occurred while generating the video extracts. Please enable verbose mode to check the ffmpeg output for more details."
            )

    def _save_summary(self) -> None:
        """
        Save the video summary to a file.
        """
        formatted_summary = MarkdownSummaryFormatter.format_summary(
            self.summary, self.summary_params.output_summary_file.parent
        )
        with open(self.summary_params.output_summary_file, "w", encoding="utf-8") as f:
            f.write(formatted_summary)


# endregion


# region Handler


class SummarizeCommandHandler(ICommandHandler):
    def __init__(self):
        self.name = "summarize"
        self.description = "Summarize a video by taking its transcript (required) and generating a detailed summary."

    def configure_args(self, parser):
        parser.add_argument(
            "-v", "--input_video", required=True, type=str, help="Input video file path."
        )
        parser.add_argument(
            "-t", "--transcript", required=True, type=str, help="Input transcript file path."
        )
        parser.add_argument(
            "-o",
            "--output_dir",
            type=str,
            help="Output directory path (where the summary will be saved with all the video extracts). If the directory does not exist, it will be created.",
        )
        parser.add_argument(
            "--openai_key",
            required=False,
            default=None,
            type=str,
            help=f"Provide a valid OpenAI API key for summarizing the video. If not provided, it will be searched in the environment variables ({OPENAI_API_KEY_ENV_VAR}). If not found, the command will fail.",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Print ffmpeg output (for debugging purposes)"
        )

    def run(self, args) -> None:
        openai_key = args.openai_key or get_env(OPENAI_API_KEY_ENV_VAR)
        if not openai_key:
            raise ValueError(
                f"OpenAI API key not provided. Please provide it as an argument or set it in the environment variable '{OPENAI_API_KEY_ENV_VAR}'."
            )

        command_params = _CommandParams(
            input_video_file=args.input_video,
            input_transcript_file=args.transcript,
            output_dir=args.output_dir,
            openai_key=openai_key,
            verbose=args.verbose,
        )
        _SummarizeCommand(command_params).execute()

        rprint(f"[bold green]Video summary saved to '{command_params.output_dir}'[/bold green]")


# endregion
