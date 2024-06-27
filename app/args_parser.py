import argparse

from app.models import CLIArgs


class ArgumentHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Help message formatter which adds default values to argument help."""

    def _get_help_string(self, action):
        """
        Add the default value to the option help message if available.

        ArgumentDefaultsHelpFormatter and BooleanOptionalAction when it isn't
        already present. This code will do that, detecting cornercases to
        prevent duplicates or cases where it wouldn't make sense to the end
        user.
        """
        help = action.help
        if help is None:
            help = ''

        default = action.default

        # Omit if default value is not given
        if default is None or default is False:
            return help

        # Format empty string default value
        if default == "":
            return help + ' (default: "")'

        if default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                help += ' (default: %(default)s)'
        return help


parser = argparse.ArgumentParser(description="Audio Transcriber")
parser.add_argument(
    "-i", "--input",
    required=True,
    type=str,
    help="Path or URL to the audio file to be transcribed.",
)
parser.add_argument(
    "-o", "--output",
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


def parse_args() -> CLIArgs:
    args = parser.parse_args()
    return CLIArgs(**args.__dict__)
