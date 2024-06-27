import argparse

from rich import print as rprint

from av_toolkit.commands import video_to_audio_converter


def _parse_args():
    parser = argparse.ArgumentParser(description="Convert video to audio.")
    parser.add_argument(
        "-i", "--input_file",
        required=True,
        type=str,
        help="Input video file path"
    )
    parser.add_argument(
        "-o", "--output_file",
        default="output.mp3",
        type=str,
        help="Output audio file path. If output file exists, it will be overwritten."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print ffmpeg output"
    )
    return parser.parse_args()


def main():
    try:
        args = _parse_args()
        command_params = video_to_audio_converter.CommandParams(
            input_file=args.input_file,
            output_file=args.output_file,
            verbose=args.verbose
        )
        video_to_audio_converter.execute(command_params)
        rprint("[bold green]Video converted to audio successfully[/bold green]")
    except KeyboardInterrupt:
        rprint("[bold red]Operation cancelled by the user.[/bold red]")
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    # Example Usage:
    # python video_to_audio.py video.mp4 -o audio.mp3
    main()
