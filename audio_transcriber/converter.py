import subprocess

from audio_transcriber.utils import file_exists

SUPPORTED_INPUT_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]
SUPPORTED_OUTPUT_EXTENSIONS = [".mp3", ".wav"]

def _is_valid_extension(file: str, extensions: list[str]) -> bool:
    return any(file.endswith(ext) for ext in extensions)

def format_extensions(extensions: list[str]) -> str:
    return ", ".join(extensions)


def convert_video_to_audio(input_file: str, output_file: str, verbose: bool = False) -> None:
    """Convert video to audio."""

    if not file_exists(input_file):
        raise FileNotFoundError(f"The file '{input_file}' does not exist.")

    if not _is_valid_extension(input_file, SUPPORTED_INPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid input file extension. Supported extensions are: {format_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
        )

    if not _is_valid_extension(output_file, SUPPORTED_OUTPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid output file extension. Supported extensions are: {format_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
        )
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        raise FileNotFoundError("ffmpeg is not installed. Please install ffmpeg before running this script.")

    # -vn: no video
    # -ac: audio channels
    output = subprocess.run([
        "ffmpeg",
        "-i", input_file,
        "-vn",
        "-ar", "44100",  # Audio rate
        "-ab", "128k",  # Audio bitrate
        "-ac", "1",
        # Overwrite output file without asking for confirmation (if it exists)
        "-y",
        output_file
    ], capture_output=True)

    if verbose:
        print(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))

    if output.returncode != 0:
        raise Exception("Error converting video to audio. Enable verbose mode for more information.")
