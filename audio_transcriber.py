from rich import print as rprint

from app.args_parser import parse_args
from app.utils import FilePath, get_env, is_supported_extension, is_url, list_extensions
import app.runner as transcriber

SUPPORTED_INPUT_EXTENSIONS = [".mp3", ".wav"]
SUPPORTED_OUTPUT_EXTENSIONS = [".json", ".txt"]


def validated_input_file(input_file) -> str:
    if is_url(input_file):
        return input_file

    input_path = FilePath(input_file)
    if not input_path.file_exists():
        raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
    if not is_supported_extension(input_path.extension, SUPPORTED_INPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid input file format: '{input_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
        )

    return str(input_path.full_path)


def validated_output_path(output_path) -> str:
    output_path = FilePath(output_path)
    if not output_path.directory_exists():
        raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
    if not is_supported_extension(output_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
        )

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
            language=args.language,
            hf_token=hf_token, # Use diarization model
        )

        rprint(f"[bold green]Transcription saved to '{args.output}'[/bold green]")
    except KeyboardInterrupt:
        rprint("[bold red]Operation cancelled by the user.[/bold red]")
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    # Example Usage:
    # python audio_transcriber.py -i video.mp4 -o output.json
    main()
