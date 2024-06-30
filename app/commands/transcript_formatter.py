from abc import ABC, abstractmethod
import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from app.models import TranscriptionChunkData, TranscriptionResultData
from app.utils import FilePath, format_duration, is_supported_extension, list_extensions


# region Formatters


class IFormatter(ABC):
    """Interface for transcript formatters."""

    @abstractmethod
    def preamble(self) -> str:
        pass

    @abstractmethod
    def format_chunk(self, chunk: TranscriptionChunkData, index: int) -> str:
        pass


class TxtFormatter(IFormatter):
    def preamble(self):
        return ""

    def format_chunk(self, chunk, index):
        return f"{chunk.text}\n"


class SrtFormatter(IFormatter):
    def preamble(self):
        return ""

    def format_chunk(self, chunk, index):
        start_format = self._format_seconds(chunk.start_time)
        end_format = self._format_seconds(chunk.end_time)
        return f"{index}\n{start_format} --> {end_format}\n{chunk.text}\n\n"

    def _format_seconds(self, seconds: float):
        return format_duration(seconds, include_milliseconds=True, milliseconds_separator=",")


class VttFormatter(IFormatter):
    def preamble(self):
        return "WEBVTT\n\n"

    def format_chunk(self, chunk, index):
        start_format = self._format_seconds(chunk.start_time)
        end_format = self._format_seconds(chunk.end_time)
        return f"{index}\n{start_format} --> {end_format}\n{chunk.text}\n\n"

    def _format_seconds(self, seconds: float):
        return format_duration(seconds, include_milliseconds=True, milliseconds_separator=".")


TRANSCRIPT_FORMATTERS = {
    ".srt": SrtFormatter(),
    ".txt": TxtFormatter(),
    ".vtt": VttFormatter(),
}

# endregion


SUPPORTED_INPUT_EXTENSIONS = [".json"]
SUPPORTED_OUTPUT_EXTENSIONS = list(TRANSCRIPT_FORMATTERS.keys())


# region Parameters


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


# endregion


def execute(params: CommandParams):
    """Convert transcript in JSON format to a subtitle file or plain text."""

    with open(params.input_file_path.full_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)
        data = TranscriptionResultData.model_validate(raw_data)

    formatter_class: IFormatter = TRANSCRIPT_FORMATTERS[params.output_file_path.extension]

    string = formatter_class.preamble()
    for index, chunk in enumerate(data.chunks, 1):
        entry = formatter_class.format_chunk(chunk, index)

        if params.verbose:
            print(entry)

        string += entry

    with open(params.output_file_path.full_path, "w", encoding="utf-8") as file:
        file.write(string)
