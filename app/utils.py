import argparse
from functools import wraps
from pathlib import Path
import os
import subprocess
from typing import Callable, Optional, ParamSpec, Union, overload
from typing_extensions import TypeVar
import dotenv
from pydantic_core import ValidationError, ErrorDetails
from rich import print as rprint
from rich.progress import Progress


# region Helper Functions


def get_env(key: str, default: str | None = None) -> str | None:
    if key in os.environ:
        return os.environ[key]

    dotenv_values = dotenv.dotenv_values()
    if dotenv_values and key in dotenv_values:
        return dotenv_values[key]

    return default


def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def is_supported_extension(extension: str, supported_extensions: list[str]) -> bool:
    """Check if the extension is supported."""
    return extension.lower() in map(str.lower, supported_extensions)


def list_extensions(extensions: list[str], separator: str = ", ") -> str:
    """Return a string with the list of supported extensions (without the dot and in uppercase)."""

    def normalize(ext):
        # Remove the dot if it exists and convert to uppercase
        normalized_ext = ext[1:] if ext.startswith(".") else ext
        return normalized_ext.upper()

    return separator.join(map(normalize, extensions))


def flatten_list(list_: list) -> list:
    """
    Flatten a list of iterables (eg. lists, tuples, etc.) into a single list.

    Remarks:
    - Non-iterable elements are not flattened.
    - This function is not recursive (only flattens the first level, not nested lists).
    """
    return [
        item
        for sublist in list_
        for item in
        (  # Only flatten the element if it is an iterable
            sublist if isinstance(sublist, (list, tuple)) else [sublist]
        )
    ]


def check_ffmpeg_installed():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        raise Exception(
            "ffmpeg is not installed. Please install ffmpeg before running this script."
        )


def format_duration(
    duration: float,
    include_milliseconds: bool = False,
    milliseconds_separator: str = ".",
) -> str:
    """
    Format the duration in seconds to a human-readable string (HH:MM:SS).
    If `include_milliseconds` is True, it will include milliseconds with the provided separator.
    """

    if duration < 0:
        raise ValueError("Duration must be a positive number.")

    whole_seconds = int(duration)
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    seconds = whole_seconds % 60

    formatted_time = f"{hours:02}:{minutes:02}:{int(seconds):02}"

    if include_milliseconds:
        milliseconds = int((duration - whole_seconds) * 1000)
        formatted_time += f"{milliseconds_separator}{milliseconds:03}"

    return formatted_time


# endregion


# region Decorators

# See https://lemonfold.io/posts/2022/dbc/typed_decorator/


def _format_validation_error(e: ValidationError, debug: bool) -> str:
    """Format a validation error as a string."""

    def clean_error_message(message: str) -> str:
        message_prefix_to_clean = "Value error, "
        return (
            message.replace(message_prefix_to_clean, "", 1)
            if message.startswith(message_prefix_to_clean)
            else message
        )

    def format_error_details(details: ErrorDetails, debug: bool) -> str:
        if debug:
            return str(details)

        cleaned_message = clean_error_message(details["msg"])
        return (
            f"{cleaned_message}"
            # f" (field: {details['loc'][0]})"
        )

    errors = e.errors(include_context=False)
    error_messages = [format_error_details(error, debug) for error in errors]

    if len(error_messages) == 1:
        return f"[bold red]Validation Error:[/bold red] {error_messages[0]}"

    return "[bold red]Validation Errors:[/bold red]\n" + "\n".join(
        [f"  - {msg}" for msg in error_messages]
    )


P = ParamSpec("P")
R = TypeVar("R")


@overload
def handle_errors(func: Callable[P, Optional[R]]) -> Callable[P, Optional[R]]: ...


@overload
def handle_errors(
    *, debug: bool
) -> Callable[[Callable[P, Optional[R]]], Callable[P, Optional[R]]]: ...


def handle_errors(
    func: Optional[Callable[P, Optional[R]]] = None, *, debug: bool = False
) -> Union[
    Callable[P, Optional[R]], Callable[[Callable[P, Optional[R]]], Callable[P, Optional[R]]]
]:
    """
    A decorator that adds exception handling.

    Parameters
    ----------
    debug : bool, optional
        If True, prints additional debug information, by default False.
        This is a keyword-only argument.

    Usage
    -----
    @handle_errors
    def my_function():
        ...

    @handle_errors(debug=True)
    def my_function():
        ...
    """

    def decorator(func: Callable[P, Optional[R]]) -> Callable[P, Optional[R]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                rprint("[bold red]Operation cancelled by the user.[/bold red]")
            except ValidationError as e:
                rprint(_format_validation_error(e, debug))
            except Exception as e:
                rprint(f"[bold red]Error:[/bold red] {e}")
                if debug:
                    raise

        return wrapper

    if func is not None:
        if not callable(func):
            raise TypeError(
                "The provided argument is not callable. Did you forget to use a keyword argument?"
            )
        return decorator(func)

    return decorator


# endregion


# region Helper Classes


class FilePath:
    """
    Class to easily handle file paths (path elements, validation and manipulation).

    Notes:
        - This class is a wrapper around the pathlib.Path class.
        - The provided path is resolved to an absolute path.
        - For directory paths or other path manipulations, use the pathlib.Path class directly
        (eg. Path('path/to/dir') / 'file.txt').
    """

    __full_path: Path

    def __init__(self, path: Path | str):
        self.__full_path = Path(path).resolve()

    # region Properties

    @property
    def full_path(self) -> Path:
        """Get the full path of the file."""
        return self.__full_path

    @property
    def directory_path(self) -> Path:
        """Get the directory path where the file is located."""
        return self.__full_path.parent

    @property
    def full_name(self) -> str:
        """Get the full name of the file (with the extension)."""
        return self.__full_path.name

    @property
    def base_name(self) -> str:
        """Get the base name of the file (without the extension)."""
        return self.__full_path.stem

    @property
    def extension(self) -> str:
        """Get the file extension including the dot."""
        return self.__full_path.suffix

    @property
    def extension_without_dot(self) -> str:
        """Get the file extension without the dot."""
        return self.__full_path.suffix[1:]

    # endregion

    # region Validation Methods

    def file_exists(self) -> bool:
        """Check if the file exists."""
        return self.__full_path.exists() and self.__full_path.is_file()

    def directory_exists(self) -> bool:
        """Check if the directory where the file should be located exists."""
        directory_path = Path(self.directory_path)
        return directory_path.exists() and directory_path.is_dir()

    # endregion

    # region Path Manipulation Methods

    def with_full_name(self, name: str) -> "FilePath":
        """Return a new FilePath with the provided full name (including the extension)."""
        return FilePath(self.__full_path.with_name(name))

    def with_base_name(self, name: str) -> "FilePath":
        """Return a new FilePath with the provided base name (without the extension)."""
        return FilePath(self.__full_path.with_stem(name))

    def with_extension(self, extension: str) -> "FilePath":
        """Return a new FilePath with the provided extension."""
        return FilePath(self.__full_path.with_suffix(extension))

    # endregion

    def __str__(self) -> str:
        return str(self.full_path)


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
            help = ""

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
                help += " (default: %(default)s)"
        return help


class PauseRichProgress:
    """
    Context manager to pause the progress bar and clear the terminal line.
    """

    def __init__(self, progress: Progress) -> None:
        self._progress = progress

    def _clear_line(self) -> None:
        UP = "\x1b[1A"
        CLEAR = "\x1b[2K"
        for _ in self._progress.tasks:
            print(UP + CLEAR + UP)

    def __enter__(self):
        self._progress.stop()
        self._clear_line()
        return self._progress

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._progress.start()


# endregion
