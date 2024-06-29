import argparse

from rich import print as rprint

from app.commands import video_summarizer
from app.utils import get_env, handle_errors

OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize a video by taking its transcript (required) and generating a detailed summary."
    )
    parser.add_argument(
        "-v", "--input_video", required=True, type=str, help="Input video file path."
    )
    parser.add_argument(
        "-t", "--transcript", required=True, type=str, help="Input transcript file path."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="Output directory path (where the summary will be saved with all the video extracts). If the directory does not exist, it will be created.",
    )
    parser.add_argument(
        "--openai_key",
        required=False,
        default=None,
        type=str,
        help=f"Provide a valid OpenAI API key for summarizing the video. If not provided, it will be searched in the environment variables ({OPENAI_API_KEY_ENV_VAR}). If not found, the command will fail.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print ffmpeg output (for debugging purposes)"
    )
    return parser.parse_args()


@handle_errors
def main():
    args = _parse_args()
    
    openai_key = args.openai_key or get_env(OPENAI_API_KEY_ENV_VAR)
    if not openai_key:
        raise ValueError(
            f"OpenAI API key not provided. Please provide it as an argument or set it in the environment variable '{OPENAI_API_KEY_ENV_VAR}'."
        )
    
    command_params = video_summarizer.CommandParams(
        input_video_file=args.input_video,
        input_transcript_file=args.transcript,
        output_dir=args.output_dir,
        openai_key=openai_key,
        verbose=args.verbose,
    )
    video_summarizer.execute(command_params)
    
    rprint(f"[bold green]Video summary saved to '{command_params.output_dir}'[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python video_summarizer.py -v /tmp/my/video/file.mp4 -t /tmp/my/transcript/file.txt -o /tmp/my/output/dir --openai_key "my_openai_key"
    main()
