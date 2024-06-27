from rich import print as rprint
from av_toolkit.args_parser import parse_args
from av_toolkit.utils import FilePath, get_env, is_url
import av_toolkit.runner as transcriber


def validated_input_file(input_file) -> str:
    if is_url(input_file):
        return input_file

    input_path = FilePath(input_file)
    if not input_path.file_exists():
        raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
    return str(input_path.full_path)


def validated_output_path(output_path) -> str:
    output_path = FilePath(output_path)
    if not output_path.directory_exists():
        raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
    return str(output_path.full_path)


def main():
    args = parse_args()
    hf_token = args.hf_token or get_env("HUGGING_FACE_TOKEN")

    try:
        input_file = validated_input_file(args.input)
        output_path = validated_output_path(args.output)

        transcriber.run(
            input_file,
            output_path,
            # hf_token=hf_token, # TODO: Uncomment this line to use diarization
        )

        rprint(f"[bold green]Transcription saved to '{args.output}'[/bold green]")
    except KeyboardInterrupt:
        rprint("[bold red]Operation cancelled by the user.[/bold red]")
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    # Example Usage:
    # python cli.py -i video.mp4 -o output.json
    main()
