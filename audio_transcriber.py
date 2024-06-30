import argparse
from rich import print as rprint

from app.utils import (
    ArgumentHelpFormatter,
    get_env,
    handle_errors,
    list_extensions,
)
from app.commands import audio_transcriber


HUGGING_FACE_TOKEN_ENV_VAR = "HUGGING_FACE_TOKEN"


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files.", formatter_class=ArgumentHelpFormatter
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
        help=f"Path to save the transcription. If not provided, the output will be saved in the same directory as the input file. Format will be inferred from the file extension. Supported formats: {list_extensions(audio_transcriber.SUPPORTED_OUTPUT_EXTENSIONS)}.",
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
        help=f"Provide a hf.co/settings/token for Pyannote.audio to diarise the audio clips. If not provided, it will be searched in the environment variables ({HUGGING_FACE_TOKEN_ENV_VAR}). If not found, diarization will be skipped. To use this feature, follow the instructions in https://huggingface.co/pyannote/speaker-diarization-3.1.",
    )
    return parser.parse_args()


@handle_errors
def main():
    args = _parse_args()
    hf_token = args.hf_token or get_env(HUGGING_FACE_TOKEN_ENV_VAR)

    command_params = audio_transcriber.CommandParams(
        input_file=args.input,
        output_file=args.output,
        language=args.language,
        hf_token=hf_token,  # Use diarization model
    )
    audio_transcriber.execute(command_params)

    rprint(f"[bold green]Transcription saved to '{args.output}'[/bold green]")


if __name__ == "__main__":
    # Example Usage:
    # python audio_transcriber.py -i video.mp4 -o output.json
    main()
