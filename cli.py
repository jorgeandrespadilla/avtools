import argparse

from rich import print as printr

from app.commands.audio_transcriber import TranscriberCommandHandler
from app.commands.transcript_formatter import FormatterCommandHandler
from app.commands.video_to_audio_converter import VideoToAudioCommandHandler
from app.models import ICommandHandler
from app.utils import ArgumentHelpFormatter, handle_errors

# List of all command handlers
COMMANDS: list[ICommandHandler] = [
    TranscriberCommandHandler(),
    FormatterCommandHandler(),
    VideoToAudioCommandHandler(),
]


def _check_commands():
    """
    Check that all command names are unique.
    """

    occurrences: dict[str, list[str]] = {}
    for command in COMMANDS:
        handler_name = command.__class__.__name__
        if command.name in occurrences:
            occurrences[command.name].append(handler_name)
        else:
            occurrences[command.name] = [handler_name]

    has_duplicates = False
    for command_name, handler_names in occurrences.items():
        if len(handler_names) > 1:
            has_duplicates = True
            printr(
                f"Duplicate command name '{command_name}' found in handlers: {', '.join(handler_names)}"
            )

    if has_duplicates:
        raise ValueError("Duplicate command names found. Specify unique names for each command.")


@handle_errors
def main():
    _check_commands()

    # Configure the CLI
    parser = argparse.ArgumentParser(
        description="AV Tools CLI",
        formatter_class=ArgumentHelpFormatter,
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Add subparsers for each command
    for command in COMMANDS:
        command_parser = subparsers.add_parser(
            command.name, help=command.description, formatter_class=ArgumentHelpFormatter
        )
        command.configure_args(command_parser)
        command_parser.set_defaults(func=command.run)

    args = parser.parse_args()

    # Run the command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
