import argparse

from audio_transcriber.models import CLIArgs


parser = argparse.ArgumentParser(description="Audio Transcriber")
parser.add_argument(
    "--input",
    required=True,
    type=str,
    help="Path or URL to the audio file to be transcribed.",
)
parser.add_argument(
    "--output",
    required=False,
    default="output.json",
    type=str,
    help="Path to save the transcribed text. Path must exist and end with '.txt' for simplified output or '.json' for detailed output. If not provided, the output will be saved in the same directory as the input file (default: 'output.json').",
)
parser.add_argument(
    "--hf-token",
    required=False,
    default=None,
    type=str,
    help="Provide a hf.co/settings/token for Pyannote.audio to diarise the audio clips. If not provided, it will be searched in the environment variables. If not found, diarization will be skipped. To use this feature, follow the instructions in https://huggingface.co/pyannote/speaker-diarization-3.1.",
)


def parse_args() -> CLIArgs:
    args = parser.parse_args()
    return CLIArgs(**args.__dict__)
