import argparse

from rich import print as rprint
from app.args_parser import ArgumentHelpFormatter
from app.commands import transcript_formatter
from app.utils import handle_errors, list_extensions


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Convert transcript in JSON format to a subtitle file or plain text.",
        formatter_class=ArgumentHelpFormatter,
    )
    parser.add_argument("-i", "--input_file", required=True, help="Input JSON file path")
    parser.add_argument(
        "-o",
        "--output_file",
        help=f"File where the output will be saved. Format will be inferred from the file extension. Supported formats: {list_extensions(transcript_formatter.SUPPORTED_OUTPUT_EXTENSIONS)}.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print each entry as it's added")
    return parser.parse_args()


@handle_errors
def main():
    args = _parse_args()
    command_params = transcript_formatter.CommandParams(
        input_file=args.input_file, output_file=args.output_file, verbose=args.verbose
    )
    transcript_formatter.execute(command_params)
    rprint("[bold green]Transcript formatted successfully[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python transcript_formatter.py -i output.json -o /tmp/my/output/file.vtt
    main()
