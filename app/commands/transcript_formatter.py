from abc import abstractmethod
import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from app.utils import FilePath, is_supported_extension, list_extensions


class IFormatter:
    @abstractmethod
    def preamble(self) -> str:
        pass

    @abstractmethod
    def format_chunk(self, chunk: dict, index) -> str:
        pass


class TxtFormatter(IFormatter):
    @classmethod
    def preamble(cls):
        return ""

    @classmethod
    def format_chunk(cls, chunk, index):
        text = chunk["text"]
        return f"{text}\n"


class SrtFormatter(IFormatter):
    @classmethod
    def preamble(cls):
        return ""

    @classmethod
    def format_chunk(cls, chunk, index):
        text = chunk["text"]
        start, end = chunk["timestamp"][0], chunk["timestamp"][1]
        start_format, end_format = cls._format_seconds(start), cls._format_seconds(end)
        return f"{index}\n{start_format} --> {end_format}\n{text}\n\n"

    @classmethod
    def _format_seconds(cls, seconds):
        whole_seconds = int(seconds)
        milliseconds = int((seconds - whole_seconds) * 1000)

        hours = whole_seconds // 3600
        minutes = (whole_seconds % 3600) // 60
        seconds = whole_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


class VttFormatter(IFormatter):
    @classmethod
    def preamble(cls):
        return "WEBVTT\n\n"

    @classmethod
    def format_chunk(cls, chunk, index):
        text = chunk["text"]
        start, end = chunk["timestamp"][0], chunk["timestamp"][1]
        start_format, end_format = cls._format_seconds(start), cls._format_seconds(end)
        return f"{index}\n{start_format} --> {end_format}\n{text}\n\n"

    @classmethod
    def _format_seconds(cls, seconds):
        whole_seconds = int(seconds)
        milliseconds = int((seconds - whole_seconds) * 1000)

        hours = whole_seconds // 3600
        minutes = (whole_seconds % 3600) // 60
        seconds = whole_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


TRANSCRIPT_FORMATTERS = {
    ".srt": SrtFormatter,
    ".txt": TxtFormatter,
    ".vtt": VttFormatter,
}

SUPPORTED_INPUT_EXTENSIONS = [".json"]
SUPPORTED_OUTPUT_EXTENSIONS = list(TRANSCRIPT_FORMATTERS.keys())


class CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_file: str
    """Input transcript file path in JSON format (do not use this field directly, use the input_file_path property instead)."""

    output_file: str
    """Output file path with the desired format (do not use this field directly, use the output_file_path property instead)."""

    verbose: bool = False
    """Enable verbose mode."""

    @computed_field
    @property
    def input_file_path(self) -> FilePath:
        return FilePath(self.input_file)

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)

    @model_validator(mode="after")
    def _validate_files(self) -> Self:
        input_path = FilePath(self.input_file)
        if not input_path.file_exists():
            raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
        if not is_supported_extension(input_path.extension, SUPPORTED_INPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid input file format: '{input_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
            )

        output_path = FilePath(self.output_file)
        if not output_path.directory_exists():
            raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
        if not is_supported_extension(output_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
            )
        return self


def execute(params: CommandParams):
    """Convert transcript in JSON format to a subtitle file or plain text."""

    with open(params.input_file_path.full_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    formatter_class: IFormatter = TRANSCRIPT_FORMATTERS[params.output_file_path.extension]

    string = formatter_class.preamble()
    for index, chunk in enumerate(data["chunks"], 1):
        entry = formatter_class.format_chunk(chunk, index)

        if params.verbose:
            print(entry)

        string += entry

    with open(params.output_file_path.full_path, "w", encoding="utf-8") as file:
        file.write(string)
