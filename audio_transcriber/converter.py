import subprocess

from audio_transcriber.utils import FilePath, is_supported_extension, list_extensions

SUPPORTED_INPUT_EXTENSIONS = [".mp4", ".mkv", ".avi", ".mov"]
SUPPORTED_OUTPUT_EXTENSIONS = [".mp3", ".wav"]


def convert_video_to_audio(input_file_str: str, output_file_str: str, verbose: bool = False):
    """Convert video to audio."""

    input_path = FilePath(input_file_str)
    output_path = FilePath(output_file_str)

    if not input_path.file_exists():
        raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
    if not is_supported_extension(input_path.extension, SUPPORTED_INPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid input file format: '{input_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
        )
    if not output_path.directory_exists():
        raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
    if not is_supported_extension(output_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
        )

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffmpeg is not installed. Please install ffmpeg before running this script.")

    # -vn: no video
    # -ac: audio channels
    output = subprocess.run([
        "ffmpeg",
        "-i", input_path.full_path,
        "-vn",
        "-ar", "44100",
        "-ab", "128k",
        "-ac", "1", # Audio channels
        # Overwrite output file without asking for confirmation (if it exists)
        "-y",
        output_path.full_path
    ], capture_output=True)

    if verbose:
        print(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))

    if output.returncode != 0:
        raise Exception(
            "Error converting video to audio. Enable verbose mode for more information."
        )
