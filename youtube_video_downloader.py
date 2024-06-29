import argparse

from rich import print as rprint

from app.commands import youtube_video_downloader
from app.utils import ArgumentHelpFormatter, handle_errors


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Download a YouTube video.",
        formatter_class=ArgumentHelpFormatter,
    )
    parser.add_argument(
        "-u", "--video_url", required=True, type=str, help="Input YouTube video URL."
    )
    parser.add_argument(
        "-o", "--output_file", default="output.mp4", type=str, help="Output video file path."
    )
    parser.add_argument(
        "-r",
        "--resolution",
        default="1080p",
        type=str,
        help=f"Target resolution for the downloaded video. Supported resolutions: {youtube_video_downloader.list_supported_resolutions()}",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print ffmpeg output (for debugging purposes)"
    )
    return parser.parse_args()


@handle_errors
def main():
    args = _parse_args()
    command_params = youtube_video_downloader.CommandParams(
        input_url=args.video_url,
        output_file=args.output_file,
        target_resolution=args.resolution,
        verbose=args.verbose,
    )
    youtube_video_downloader.execute(command_params)
    rprint(f"[bold green]Video downloaded to '{command_params.output_file_path}'[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python youtube_video_downloader.py -i https://www.youtube.com/watch?v=VIDEO_ID -o /tmp/my/output/file.mp4 -r 720p
    main()
