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
    help="Path to save the transcribed text (path must exist and end with '.json'). If not provided, the output will be saved in the same directory as the input file (default: 'output.txt').",
)
parser.add_argument(
    "--hf-token",
    required=False,
    default=None,
    type=str,
    help="Provide a hf.co/settings/token for Pyannote.audio to diarise the audio clips. If not provided, it will be searched in the environment variables. If not found, diarization will be skipped. To use this feature, you must have a Hugging Face account and accept the conditions of the model you want to use (by default pyannote/speaker-diarization-3.1).",
)


def parse_args() -> CLIArgs:
    args = parser.parse_args()
    return CLIArgs(**args.__dict__)
