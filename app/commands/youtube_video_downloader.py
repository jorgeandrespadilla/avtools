import json
from pathlib import Path
import subprocess
import tempfile
from typing import Literal
from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from pytube import YouTube, StreamQuery, Stream, exceptions
from rich import print as printr
from rich.progress import (
    Progress,
    TimeElapsedColumn,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    TaskProgressColumn,
    TaskID
)
from typing_extensions import Self
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

from app.utils import FilePath, check_ffmpeg_installed, flatten_list, is_supported_extension, is_url, list_extensions

SUPPORTED_OUTPUT_EXTENSIONS = [".mp4"]
SUPPORTED_RESOLUTIONS = ["360p", "480p", "720p", "1080p", "1440p"]


class CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_url: str
    """Input video URL."""

    output_file: str
    """Output video file path (do not use this field directly, use the output_file_path property instead)."""

    target_resolution: str = "1080p"
    """Target resolution for the downloaded video."""

    transcript: str | None = None
    """Include transcript file in the output folder (same name as the video file, but in JSON format) with the specified language code (eg. 'en')."""

    verbose: bool = False
    """Enable verbose mode."""

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)
    
    @computed_field
    @property
    def include_transcript(self) -> bool:
        return self.transcript is not None

    @computed_field
    @property
    def transcript_file_path(self) -> FilePath:
        """Transcript file path."""
        if not self.include_transcript:
            raise ValueError("Transcript file path is not available because 'include_transcript' is False.")
        return self.output_file_path.with_extension(".json")

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


def _sort_resolutions(resolutions: list[str]) -> list[str]:
    """Sort the resolutions by quality (ascending order)."""
    return sorted(resolutions, key=lambda x: int(x[:-1]))


def _list_resolutions(resolutions: list[str], separator: str = ", ") -> str:
    """Return a string with the list of resolutions (sorted by quality)."""
    return separator.join(_sort_resolutions(resolutions))


def list_supported_resolutions() -> str:
    """Return a string with the list of supported resolutions."""
    return _list_resolutions(SUPPORTED_RESOLUTIONS)


def _get_available_resolutions(streams: StreamQuery) -> list[str]:
    """Return a list with the available resolutions for the video streams."""
    video_streams = streams.filter(type="video")
    available_resolutions = list(set([stream.resolution for stream in video_streams]))
    return _sort_resolutions(available_resolutions)


class MediaStreams:
    """
    Streams to download (video and audio).

    Parameters:
    - video: Video stream to download.
    - audio: Audio stream to download (optional).

    Remarks:
    - If the video stream is progressive, only includes the video stream.
    - If the video stream is adaptive, includes both the video stream and the audio stream.
    - If the video stream is adaptive and no audio stream is found, only includes the video stream.
    """

    def __init__(self, video: Stream, audio: Stream | None):
        self.video = video
        self.audio = audio

    def stream_type(self) -> Literal["progressive", "adaptive"]:
        """Return the type of the video stream."""
        return "progressive" if self.video.is_progressive else "adaptive"
    
    def has_audio(self) -> bool:
        """
        Check if the video stream has an audio stream.
        We assume that any progressive stream has audio (even if the video has no audio).
        """
        if self.video.is_progressive: # Video + audio in a single file
            return True
        return self.audio is not None
    
    def download_video(self, output_path: FilePath) -> str:
        """
        Download the video stream.
        
        Parameters:
        - output_path: Output file path.

        Returns:
        - The path to the downloaded video file.
        """
        return self.video.download(
            output_path=str(output_path.directory_path),
            filename=output_path.full_name,
            skip_existing=False, # Always download the video stream
        )
    
    def download_audio(self, output_path: FilePath) -> str:
        """
        Download the audio stream.
        
        Parameters:
        - output_path: Output file path.

        Returns:
        - The path to the downloaded audio file.
        """
        if self.audio is None:
            raise ValueError("No audio stream found.")
        return self.audio.download(
            output_path=str(output_path.directory_path),
            filename=output_path.full_name,
            skip_existing=False, # Always download the audio stream
        )


class DownloadCommand:
    """
    Download a YouTube video.
    """

    """
    Steps to download the video:
    1. [FORMAT] Filter all the streams by file_extension=MP4 (streams).
        1.1. If no streams are found, raise an error ("No MP4 video stream found.")
    2. [STREAMS]
        2.1. [VIDEO] Filter the streams by resolution=target_resolution (video_streams). When filtering by resolution, only video streams are considered.
            2.1.1. If no video_streams are found, raise an error ("No video stream found with resolution '{target_resolution}'.")
            2.1.2. If video_streams is not empty:
                2.2.1. If only progressive streams are found (video + audio in a single file), choose the first one [CONTINUE TO STEP 3] (stream.is_progressive) and skip the audio stream.
                2.2.2. If there is any adaptive stream (only video), choose the first one (stream.is_adaptive). Now we need to get the audio stream. [CONTINUE TO STEP 2.2]
        2.2. [AUDIO] Filter all the streams by only_audio=True (audio_streams).
            3.1 If no audio_streams are found, print a warning ("No audio stream found. The video will be downloaded without audio."). Probably the video has no audio. [CONTINUE TO STEP 3]
            3.2 If audio_streams is not empty, choose the one with the highest bitrate order_by("abr").desc().first(). We always download the audio stream with the highest quality. [CONTINUE TO STEP 3]
    3. [DOWNLOAD] Download the video and audio streams.
        3.1. If only the video stream is found, download directly the video stream (save to desired output file path). [END OF PROCESS]
        3.2. Download the video stream (save to temporary file path).
        3.3. If the audio stream is not None, download the audio stream (save to temporary file path).
    4. [MERGE] Merge the video and audio files using ffmpeg.
        4.1. Merge the video and audio files using ffmpeg (save to the desired output file path).
    5. [CLEANUP] Remove the temporary files (video and audio). Handle errors to ensure the cleanup is always executed. [END OF PROCESS]
    """

    def __init__(self, params: CommandParams):
        self.params = params

    def execute(self) -> None:
        """
        Execute the command.
        """

        check_ffmpeg_installed()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="yellow1", pulse_style="white"),
            TaskProgressColumn(),
            "",
            TimeElapsedColumn(),
        ) as progress:
            # Fetch the video
            fetch_task = progress.add_task("[yellow]Fetching video...", total=None)
            yt = self._fetch_video()
            media_streams = self._select_streams(yt)
            if not media_streams.has_audio():
                printr("No audio stream found. The video will be downloaded without audio.")
            progress.update(
                fetch_task, 
                description="[green]Video fetched successfully", 
                completed=1,
                total=1,
                visible=self.params.verbose
            )

            # Show video information
            printr(f"[bold]Title:[/bold] '{yt.title}'")
            printr(f"[bold]Channel:[/bold] '{yt.author}'")

            # Download the video and audio streams
            if not media_streams.audio:
                # Download video only and save to the output file path
                self._register_progress_callbacks(yt, progress, media_streams.video.filesize, "[yellow]Downloading video...", "[green]Video download completed")
                media_streams.download_video(self.params.output_file_path)
                return

            with tempfile.TemporaryDirectory() as temp_dir:
                # Download video and audio streams to temporary files
                self._register_progress_callbacks(yt, progress, media_streams.video.filesize, "[yellow]Downloading video...", "[green]Video download completed")
                temp_video_path = media_streams.download_video(FilePath(Path(temp_dir) / "video.mp4"))
                
                self._register_progress_callbacks(yt, progress, media_streams.audio.filesize, "[yellow]Downloading audio...", "[green]Audio download completed")
                temp_audio_path = media_streams.download_audio(FilePath(Path(temp_dir) / "audio.mp4"))

                # Merge video and audio files
                merge_task = progress.add_task("[yellow]Merging video and audio...", total=None)
                self._merge_video_and_audio(
                    video_file_path=temp_video_path,
                    audio_file_path=temp_audio_path,
                )
                progress.update(
                    merge_task,
                    description="[green]Media merged successfully",
                    visible=self.params.verbose,
                )
            
            # Download the transcript file
            fetch_task = progress.add_task("[yellow]Downloading transcript...", total=None)
            self._download_transcript(yt)
            progress.update(
                fetch_task, 
                description="[green]Transcript download completed",
                completed=1,
                total=1
            )

    def _fetch_video(self) -> YouTube:
        """	
        Fetch the video from the provided URL.	
        """
        try:
            yt = YouTube(self.params.input_url)
        except exceptions.RegexMatchError as e:
            raise ValueError("Invalid YouTube video URL. Please provide a valid URL.") from e
        self._check_availability(yt)
        return yt

    def _check_availability(self, yt: YouTube) -> None:
        """
        Check the availability of the video. If the video is not available, raise an exception with the corresponding error message.
        """
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

    def _select_streams(self, yt: YouTube) -> MediaStreams:
        """Select the video and audio streams to download."""

        # Find MP4 streams
        streams = yt.streams.filter(file_extension="mp4")
        if not streams:
            raise ValueError("No MP4 video stream found.")

        # Find video stream with the target resolution
        video_streams = streams.filter(res=self.params.target_resolution)
        if not video_streams:
            available_resolutions = _get_available_resolutions(streams)
            raise ValueError(
                f"No MP4 video stream found with resolution '{self.params.target_resolution}'. Available resolutions: {_list_resolutions(available_resolutions)}"
            )
        # Check if only progressive streams are available
        only_progressive = all([stream.is_progressive for stream in video_streams])
        if only_progressive: # Video + audio in a single file
            video_stream = video_streams.first()
            if not video_stream:
                raise ValueError("Failed to find a progressive video stream (this should not happen).")
            return MediaStreams(video=video_stream, audio=None)
        # Find the first adaptive video stream
        video_stream = video_streams.filter(adaptive=True).first()
        if not video_stream:
            raise ValueError("Failed to find an adaptive video stream (this should not happen).")

        # Find the audio stream with the highest quality
        audio_stream = streams \
            .filter(only_audio=True) \
            .order_by("abr") \
            .desc() \
            .first()
        if not audio_stream:
            return MediaStreams(video=video_stream, audio=None)
        return MediaStreams(video=video_stream, audio=audio_stream)
    
    def _register_progress_callbacks(
        self,
        yt: YouTube,
        progress: Progress,
        download_filesize: int,
        progress_message: str = "[yellow]Downloading stream...",
        completed_message: str = "[green]Download completed",
    ) -> TaskID:
        """
        Register progress callbacks for the download process.

        Returns:
        - The task ID.
        """

        task = progress.add_task(progress_message, total=download_filesize)

        def on_progress_callback(stream: Stream, _chunk, bytes_remaining: int):
            # printr("file_size: ", stream.filesize, "bytes_remaining: ", bytes_remaining)
            current_progress = stream.filesize - bytes_remaining
            progress.update(task, completed=current_progress)
        yt.register_on_progress_callback(on_progress_callback)

        def on_complete_callback(stream: Stream, _file_handle):
            progress.update(task, completed=stream.filesize, description=completed_message)
        yt.register_on_complete_callback(on_complete_callback)

        return task
    
    def _download_transcript(self, yt: YouTube) -> None:
        """Download the transcript file with the video subtitles."""
        if not self.params.transcript:
            return
        
        available_transcripts = YouTubeTranscriptApi.list_transcripts(yt.video_id)
        if not available_transcripts:
            raise Exception("No transcript found for the video.")
        
        available_language_codes = [
            str(transcript.language_code).lower()
            for transcript in available_transcripts
        ]
        if self.params.transcript.lower() not in available_language_codes:
            raise ValueError(
                f"Transcript not found for the video with language code '{self.params.transcript}'. Available language codes: {', '.join(available_language_codes)}."
            )
        
        try:
            raw_transcript = YouTubeTranscriptApi.get_transcript(
                yt.video_id,
                languages=(self.params.transcript,)
            )
        except NoTranscriptFound:
            raise Exception("No transcript found for the video with language code '{self.params.transcript}'. Please try another language code.")

        formatted_transcript = self._format_raw_transcript(raw_transcript)
        with open(self.params.transcript_file_path.full_path, "w", encoding="utf8") as file:
            json.dump(formatted_transcript, file, ensure_ascii=False)

    def _format_raw_transcript(self, raw_transcript: list[dict]) -> dict:
        """
        Format the raw transcript data to standard format.
        """
        text = ""
        chunks = []
        for item in raw_transcript:
            if "text" not in item:
                continue
            start = item["start"]
            end = start + item["duration"]
            text += " " + item["text"]
            chunks.append({
                "timestamp": [start, end],
                "text": item["text"],
            })
        return {
            "speakers": [],
            "chunks": chunks,
            "text": text.strip(),
        }

    def _merge_video_and_audio(self, video_file_path: str, audio_file_path: str):
        """Merge the video and audio files using ffmpeg."""

        command_args = flatten_list([
            ("-i", video_file_path),  # Input video file
            ("-i", audio_file_path),  # Input audio file
            ("-map", "0:v"),  # Video stream from the first input file (video)
            ("-map", "1:a"),  # Audio stream from the second input file (audio)
            ("-c:v", "copy"),  # Copy video codec
            ("-c:a", "aac"),  # AAC audio codec
            ("-filter:a", "loudnorm"), # Normalize the audio volume
            "-y",  # Overwrite output file without asking for confirmation (if it exists)
            str(self.params.output_file_path.full_path),  # Output file
        ])
        output = subprocess.run(["ffmpeg", *command_args], capture_output=True)

        if self.params.verbose:
            printr(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))
        if output.returncode != 0:
            raise Exception(
                "An error occurred while merging the video and audio files. Please enable verbose mode to check the ffmpeg output for more details."
            )


def execute(params: CommandParams) -> None:
    """
    Download a YouTube video.

    Remarks:
    - The video is downloaded with the highest audio quality available.
    """
    DownloadCommand(params).execute()
