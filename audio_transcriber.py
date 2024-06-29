import argparse
from pydantic import BaseModel
from rich import print as rprint

from app.utils import (
    ArgumentHelpFormatter,
    FilePath,
    get_env,
    handle_errors,
    is_supported_extension,
    is_url,
    list_extensions,
)
from app.commands import audio_transcriber


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Audio Transcriber", formatter_class=ArgumentHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path or URL to the audio file to be transcribed.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        default="output.json",
        type=str,
        help="Path to save the transcribed text. Path must exist and end with '.txt' for simplified output or '.json' for detailed output. If not provided, the output will be saved in the same directory as the input file (default: 'output.json').",
    )
    parser.add_argument(
        "--language",
        required=False,
        default=None,
        type=str,
        help="Provide the language code for the audio file (eg. 'en', 'es'). If not provided, the language will be detected automatically. For a list of supported languages, visit https://github.com/openai/whisper#available-models-and-languages.",
    )
    parser.add_argument(
        "--hf-token",
        required=False,
        default=None,
        type=str,
        help="Provide a hf.co/settings/token for Pyannote.audio to diarise the audio clips. If not provided, it will be searched in the environment variables. If not found, diarization will be skipped. To use this feature, follow the instructions in https://huggingface.co/pyannote/speaker-diarization-3.1.",
    )
    return parser.parse_args()


class CLIArgs(BaseModel):
    input: str
    output: str
    language: str | None = None
    hf_token: str | None = None


def validated_input_file(input_file) -> str:
    if is_url(input_file):
        return input_file

    input_path = FilePath(input_file)
    if not input_path.file_exists():
        raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
    if not is_supported_extension(
        input_path.extension, audio_transcriber.SUPPORTED_INPUT_EXTENSIONS
    ):
        raise ValueError(
            f"Invalid input file format: '{input_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(audio_transcriber.SUPPORTED_INPUT_EXTENSIONS)}"
        )

    return str(input_path.full_path)


def validated_output_path(output_path) -> str:
    output_path = FilePath(output_path)
    if not output_path.directory_exists():
        raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
    if not is_supported_extension(
        output_path.extension, audio_transcriber.SUPPORTED_OUTPUT_EXTENSIONS
    ):
        raise ValueError(
            f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(audio_transcriber.SUPPORTED_OUTPUT_EXTENSIONS)}"
        )

    return str(output_path.full_path)


@handle_errors
def main():
    args = _parse_args()
    args = CLIArgs(**args.__dict__)
    hf_token = args.hf_token or get_env("HUGGING_FACE_TOKEN")

    input_file = validated_input_file(args.input)
    output_path = validated_output_path(args.output)

    audio_transcriber.execute(
        input_file,
        output_path,
        language=args.language,
        hf_token=hf_token,  # Use diarization model
    )

    rprint(f"[bold green]Transcription saved to '{args.output}'[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python audio_transcriber.py -i video.mp4 -o output.json
    main()
