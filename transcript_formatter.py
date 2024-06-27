import argparse

from rich import print as rprint
from av_toolkit.args_parser import ArgumentHelpFormatter
from av_toolkit.formatter import SUPPORTED_OUTPUT_EXTENSIONS, format_transcript
from av_toolkit.utils import list_extensions


def main():
    parser = argparse.ArgumentParser(
        description="Convert transcript in JSON format to a subtitle file or plain text.",
        formatter_class=ArgumentHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input_file",
        required=True,
        help="Input JSON file path"
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help=f"File where the output will be saved. Format will be inferred from the file extension. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each entry as it's added"
    )
    args = parser.parse_args()

    try:
        format_transcript(args.input_file, args.output_file, args.verbose)
        rprint("[bold green]Transcript formatted successfully[/bold green]")
    except KeyboardInterrupt:
        rprint("[bold red]Operation cancelled by the user.[/bold red]")
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")



if __name__ == "__main__":
    # Example Usage:
    # python transcript_formatter.py -i output.json -o /tmp/my/output/file.vtt
    main()
