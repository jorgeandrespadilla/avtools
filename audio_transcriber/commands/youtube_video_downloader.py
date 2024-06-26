from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from pytube import YouTube, exceptions
from rich import print as printr
from rich.progress import (
    Progress,
    TimeElapsedColumn,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    TaskProgressColumn,
)
from typing_extensions import Self

from audio_transcriber.utils import FilePath, is_supported_extension, is_url, list_extensions

YOUTUBE_FILE_EXTENSION = "mp4"
SUPPORTED_OUTPUT_EXTENSIONS = [".mp4"]
SUPPORTED_RESOLUTIONS = ["360p", "480p", "720p", "1080p", "1440p"]



def _sort_resolutions(resolutions: list[str]) -> list[str]:
    """Sort the resolutions by quality (ascending order)."""
    return sorted(resolutions, key=lambda x: int(x[:-1]))


def _list_resolutions(resolutions: list[str], separator: str = ", ") -> str:
    """Return a string with the list of resolutions (sorted by quality)."""
    return separator.join(_sort_resolutions(resolutions))


def list_supported_resolutions() -> str:
    """Return a string with the list of supported resolutions."""
    return _list_resolutions(SUPPORTED_RESOLUTIONS)


class CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_url: str
    """Input video URL."""

    output_file: str
    """Output video file path (do not use this field directly, use the output_file_path property instead)."""

    target_resolution: str = "1080p"
    """Target resolution for the downloaded video."""

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)

    @model_validator(mode="after")
    def _validate_fields(self) -> Self:
        if not is_url(self.input_url):
            raise ValueError("Invalid input URL. Please provide a valid URL.")

        if not is_supported_extension(self.output_file_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
            raise ValueError(
                f"Unsupported output file format: '{self.output_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
            )
        if not self.output_file_path.directory_exists():
            raise FileNotFoundError(
                f"Directory not found: '{self.output_file_path.directory_path}'"
            )
        
        if self.target_resolution not in SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"Invalid target resolution: '{self.target_resolution}'. Supported resolutions: {list_supported_resolutions()}"
            )
        
        return self


def _check_availability(yt: YouTube) -> None:
    try:
        yt.check_availability()
    except exceptions.MembersOnly as e:
        raise Exception("The provided video is only available for members.") from e
    except exceptions.RecordingUnavailable as e:
        raise Exception(
            "The provided video does not have a live stream recording available."
        ) from e
    except exceptions.VideoPrivate as e:
        raise Exception("The provided video is private.") from e
    except exceptions.LiveStreamError as e:
        raise Exception("The provided video is a live stream.") from e
    except exceptions.VideoUnavailable as e:
        raise Exception("The provided video is unavailable.") from e
    except Exception as e:
        raise Exception("An error occurred while checking the video availability.") from e


def _get_available_resolutions(yt: YouTube) -> list[str]:
    video_streams = yt.streams.filter(file_extension=YOUTUBE_FILE_EXTENSION, type="video")
    available_resolutions = list(set([stream.resolution for stream in video_streams]))
    return _sort_resolutions(available_resolutions)


def execute(params: CommandParams) -> None:
    """
    Download a YouTube video.

    Remarks:
    - The video is downloaded with the highest audio quality available.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(style="yellow1", pulse_style="white"),
        TaskProgressColumn(),
        "",
        TimeElapsedColumn(),
    ) as progress:
        fetch_task = progress.add_task("[yellow]Fetching video...", total=None)
        download_task = progress.add_task("[yellow]Downloading video...", total=1, completed=0, visible=False)

        # Download the video
        def on_progress_callback(stream, _chunk, bytes_remaining):
            # printr("file_size: ", stream.filesize, "bytes_remaining: ", bytes_remaining)
            current_progress = stream.filesize - bytes_remaining
            progress.update(
                download_task,
                completed=current_progress,
            )

        def on_complete_callback(stream, _file_handle):
            progress.update(
                download_task, completed=stream.filesize, description="[green]Download completed"
            )

        try:
            yt = YouTube(
                params.input_url,
                on_progress_callback=on_progress_callback,
                on_complete_callback=on_complete_callback,
            )
        except exceptions.RegexMatchError as e:
            raise ValueError("Invalid YouTube video URL. Please provide a valid URL.") from e

        _check_availability(yt)

        """
        Process to download the video:
        1. [FORMAT] Filter all the streams by file_extension=MP4 (streams).
            1.1 If no streams are found, raise an error ("No MP4 video stream found.")
        2. [VIDEO] Filter the streams by resolution=target_resolution (video_streams). When filtering by resolution, only video streams are considered.
            2.1 If no video_streams are found, raise an error ("No video stream found with resolution '{target_resolution}'.")
            2.2. If video_streams is not empty:
                2.2.1. If only progressive streams are found (video + audio in a single file), download the first one [END OF PROCESS] (stream.is_progressive) (save to the desired output file path).
                2.2.2. If there is any adaptive stream (only video), download the first one (save the video to temporary file path) (stream.is_adaptive). Now we need to download the audio stream. [CONTINUE]
        3. [AUDIO] Filter all the streams by only_audio=True (audio_streams).
            3.1 If no audio_streams are found, print a warning ("No audio stream found. The video will be downloaded without audio."). Probably the video has no audio. [CONTINUE]
            3.2 If audio_streams is not empty, download the one with the highest bitrate order_by("abr").desc().first() (save the audio to temporary file path). We always download the audio stream with the highest quality. [CONTINUE]
        4. [MERGE] Merge the video and audio files using ffmpeg.
            4.1 If the audio file path is None, the video file is already complete. [END OF PROCESS]
            4.2 If the audio file path is not None, merge the video and audio files using ffmpeg (save to the desired output file path). [END OF PROCESS]
        """

        streams = yt.streams.filter(file_extension=YOUTUBE_FILE_EXTENSION)
        if not streams:
            raise ValueError("No MP4 video stream found.")
        
        video_stream = streams.filter(res=params.target_resolution).first()
        if video_stream is None:
            available_resolutions = _get_available_resolutions(yt)
            raise ValueError(
                f"No MP4 video stream found with resolution '{params.target_resolution}'. Available resolutions: {_list_resolutions(available_resolutions)}"
            )
        
        progress.update(fetch_task, visible=False)

        printr(f"[bold]Title:[/bold] '{yt.title}'")
        printr(f"[bold]Channel:[/bold] '{yt.author}'")

        # Update the total size for the progress bar based on the video file size
        progress.update(download_task, total=video_stream.filesize, visible=True)

        video_stream.download(
            str(params.output_file_path.directory_path),
            filename=params.output_file_path.full_name,
            skip_existing=False # Do not skip the download if the file already exists
        )
