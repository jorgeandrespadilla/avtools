import os
import dotenv
import subprocess


def get_env(key: str, default: str | None = None) -> str | None:
    if key in os.environ:
        return os.environ[key]

    dotenv_values = dotenv.dotenv_values()
    if dotenv_values and key in dotenv_values:
        return dotenv_values[key]

    return default


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def convert_video_to_audio(input_file: str, output_file: str, verbose: bool = False) -> None:
    """Convert video to audio."""

    # -vn: no video
    # -ac: audio channels
    output = subprocess.run([
        "ffmpeg",
        "-i", input_file,
        "-vn",
        "-ar", "44100", # Audio rate
        "-ab", "128k", # Audio bitrate
        "-ac", "1",
        "-y",
        output_file
    ], capture_output=True)

    if verbose:
        print(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))

    if output.returncode != 0:
        raise Exception("Error converting video to audio")
