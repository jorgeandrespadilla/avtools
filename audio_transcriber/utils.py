from pathlib import Path
import os
import dotenv


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
    """Return a string with the list of supported extensions."""
    def normalize(ext):
        # Remove the dot if it exists and convert to uppercase
        normalized_ext = ext[1:] if ext.startswith(".") else ext
        return normalized_ext.upper()
    return separator.join(map(normalize, extensions))


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path) and os.path.isfile(file_path)


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


    def with_full_name(self, name: str) -> 'FilePath':
        """Return a new FilePath with the provided full name (including the extension)."""
        return FilePath(self.__full_path.with_name(name))

    def with_base_name(self, name: str) -> 'FilePath':
        """Return a new FilePath with the provided base name (without the extension)."""
        return FilePath(self.__full_path.with_stem(name))

    def with_extension(self, extension: str) -> str:
        """Return a new FilePath with the provided extension."""
        return str(self.__full_path.with_suffix(extension))

# endregion

    def __str__(self) -> str:
        return str(self.full_path)
