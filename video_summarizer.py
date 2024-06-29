import argparse

from rich import print as rprint

from app.commands import video_summarizer
from app.utils import handle_errors


def _parse_args():
    parser = argparse.ArgumentParser(description="Summarize a video by taking its transcript (required) and generating a detailed summary.")
    parser.add_argument(
        "-v", "--input_video",
        required=True,
        type=str,
        help="Input video file path."
    )
    parser.add_argument(
        "-t", "--transcript",
        required=True,
        type=str,
        help="Input transcript file path."
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        help="Output directory path (where the summary will be saved with all the video extracts). If the directory does not exist, it will be created."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print ffmpeg output (for debugging purposes)"
    )
    return parser.parse_args()


@handle_errors
def main():
    args = _parse_args()
    command_params = video_summarizer.CommandParams(
        input_video_file=args.input_video,
        input_transcript_file=args.transcript,
        output_dir=args.output_dir,
        verbose=args.verbose
    )
    video_summarizer.execute(command_params)
    rprint(f"[bold green]Video summary saved to '{command_params.output_dir}'[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python video_summarizer.py -v /tmp/my/video/file.mp4 -t /tmp/my/transcript/file.txt -o /tmp/my/output/dir
    main()
