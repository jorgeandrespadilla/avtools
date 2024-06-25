import argparse

from rich import print as rprint

from audio_transcriber.commands import youtube_video_downloader


def _parse_args():
    parser = argparse.ArgumentParser(description="Download a YouTube video.")
    parser.add_argument(
        "-i", "--video_url",
        required=True,
        type=str,
        help="Input YouTube video URL."
    )
    parser.add_argument(
        "-o", "--output_file",
        default="output.mp4",
        type=str,
        help="Output video file path."
    )
    parser.add_argument(
        "-r", "--resolution",
        default="1080p",
        type=str,
        help=f"Target resolution for the downloaded video. Supported resolutions: {youtube_video_downloader.list_resolutions()}"
    )
    return parser.parse_args()


def main():
    try:
        args = _parse_args()
        command_params = youtube_video_downloader.CommandParams(
            input_url=args.video_url,
            output_file=args.output_file,
            target_resolution=args.resolution
        )
        youtube_video_downloader.execute(command_params)
        rprint(f"[bold green]Video downloaded to '{command_params.output_file_path}' successfully[/bold green]")
    except KeyboardInterrupt:
        rprint("[bold red]Operation cancelled by the user.[/bold red]")
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    # Example Usage:
    # python youtube_video_downloader.py -i https://www.youtube.com/watch?v=VIDEO_ID -o /tmp/my/output/file.mp4 -r 720p
    main()
