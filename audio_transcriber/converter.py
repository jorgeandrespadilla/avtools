import subprocess

def convert_video_to_audio(input_file: str, output_file: str, verbose: bool = False) -> None:
    """Convert video to audio."""

    # -vn: no video
    # -ac: audio channels
    output = subprocess.run([
        "ffmpeg",
        "-i", input_file,
        "-vn",
        "-ar", "44100",  # Audio rate
        "-ab", "128k",  # Audio bitrate
        "-ac", "1",
        "-y", # Overwrite output file without asking for confirmation (if it exists)
        output_file
    ], capture_output=True)

    if verbose:
        print(output.stdout.decode("utf-8") or output.stderr.decode("utf-8"))

    if output.returncode != 0:
        raise Exception("Error converting video to audio")
