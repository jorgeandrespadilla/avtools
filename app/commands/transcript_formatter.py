from abc import ABC, abstractmethod
import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from rich import print as printr

from app.models import TranscriptionChunkData, TranscriptionResultData
from app.utils import FilePath, format_duration, is_supported_extension, list_extensions


# region Formatters


class IFormatter(ABC):
    """Interface for transcript formatters."""

    @abstractmethod
    def format(self, data: TranscriptionResultData, verbose: bool = False) -> str:
        """Format the transcription data."""
        pass


class TxtFormatter(IFormatter):
    """
    Convert the transcription to a TXT format.

    Remarks
    ----
    - If speaker data is available, use the speaker format. Otherwise, use the chunk format.
    """

    def format(self, data, verbose=False):
        chunks = data.speakers if data.speakers else data.chunks

        if verbose:
            printr("Speaker data available.") if data.speakers else printr(
                "No speaker data available, using chunk data."
            )

        string = ""
        for chunk in chunks:
            entry = f"{chunk}\n\n"
            string += entry
            if verbose:
                printr(entry)
        return string


class SrtFormatter(IFormatter):
    """Convert the transcription to a SRT format."""

    def format(self, data, verbose=False):
        string = ""
        for index, chunk in enumerate(data.chunks, 1):
            entry = self._format_chunk(chunk, index)
            string += entry
            if verbose:
                printr(entry)
        return string

    def _format_chunk(self, chunk: TranscriptionChunkData, index: int) -> str:
        start_format = self._format_seconds(chunk.start_time)
        end_format = self._format_seconds(chunk.end_time)
        return f"{index}\n{start_format} --> {end_format}\n{chunk.text}\n\n"

    def _format_seconds(self, seconds: float) -> str:
        return format_duration(seconds, include_milliseconds=True, milliseconds_separator=",")


class VttFormatter(IFormatter):
    """Convert the transcription to a VTT format."""

    def format(self, data, verbose=False):
        string = "WEBVTT\n\n"
        for index, chunk in enumerate(data.chunks, 1):
            entry = self._format_chunk(chunk, index)
            string += entry
            if verbose:
                printr(entry)
        return string

    def _format_chunk(self, chunk: TranscriptionChunkData, index: int) -> str:
        start_format = self._format_seconds(chunk.start_time)
        end_format = self._format_seconds(chunk.end_time)
        return f"{index}\n{start_format} --> {end_format}\n{chunk.text}\n\n"

    def _format_seconds(self, seconds: float) -> str:
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

    # Additional parameters
    group_by_speaker: bool = True
    """Group the transcript by speaker (only applicable for TXT format if speaker data is available)."""

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
        data = TranscriptionResultData.model_validate(json.load(file))

    if params.group_by_speaker:
        data = data.group_by_speaker()

    formatter_class: IFormatter = TRANSCRIPT_FORMATTERS[params.output_file_path.extension]
    formatted_transcription = formatter_class.format(data, params.verbose)

    with open(params.output_file_path.full_path, "w", encoding="utf-8") as file:
        file.write(formatted_transcription)
