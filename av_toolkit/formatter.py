from abc import abstractmethod
import json

from av_toolkit.utils import FilePath, is_supported_extension, list_extensions


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

SUPPORTED_OUTPUT_EXTENSIONS = list(TRANSCRIPT_FORMATTERS.keys())


def format_transcript(input_path_str: str, output_path_str: str, verbose=False):
    """Convert transcript in JSON format to a subtitle file or plain text."""

    input_path = FilePath(input_path_str)
    output_path = FilePath(output_path_str)

    # Validate input and output paths
    if not input_path.file_exists():
        raise FileNotFoundError(f"File not found: '{input_path.full_path}'")
    if not input_path.extension == ".json":
        raise ValueError("Input file must be a JSON file.")
    if not output_path.directory_exists():
        raise FileNotFoundError(f"Directory not found: '{output_path.directory_path}'")
    if not is_supported_extension(output_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
        raise ValueError(
            f"Invalid output file format: '{output_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
        )

    with open(input_path.full_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    formatter_class: IFormatter = TRANSCRIPT_FORMATTERS[output_path.extension]

    string = formatter_class.preamble()
    for index, chunk in enumerate(data["chunks"], 1):
        entry = formatter_class.format_chunk(chunk, index)

        if verbose:
            print(entry)

        string += entry

    with open(output_path.full_path, "w", encoding="utf-8") as file:
        file.write(string)
