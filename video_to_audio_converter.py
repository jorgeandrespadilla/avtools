import argparse

from rich import print as rprint
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn

from audio_transcriber.converter import convert_video_to_audio


def main():
    parser = argparse.ArgumentParser(description="Convert video to audio.")
    parser.add_argument(
        "input_file",
        help="Input video file path"
    )
    parser.add_argument(
        "-o", "--output_file",
        default="output.mp3",
        help="Output audio file path. If output file exists, it will be overwritten."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print ffmpeg output"
    )
    args = parser.parse_args()

    try:
        with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(style="yellow1", pulse_style="white"),
                TimeElapsedColumn(),
        ) as progress:
            progress.add_task(
                "[yellow]Converting video to audio...", total=None)
            convert_video_to_audio(
                args.input_file, args.output_file, args.verbose)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    # Example Usage:
    # python video_to_audio.py video.mp4 -o audio.mp3
    main()
