from abc import abstractmethod
import json
import os


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
        text = chunk['text']
        return f"{text}\n"


class SrtFormatter(IFormatter):
    @classmethod
    def preamble(cls):
        return ""


    @classmethod
    def format_chunk(cls, chunk, index):
        text = chunk['text']
        start, end = chunk['timestamp'][0], chunk['timestamp'][1]
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
        text = chunk['text']
        start, end = chunk['timestamp'][0], chunk['timestamp'][1]
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


def format_transcript(input_path: str, output_format: str, output_path: str, verbose=False):
    with open(input_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    formatters = {
        'srt': SrtFormatter,
        'vtt': VttFormatter,
        'txt': TxtFormatter
    }
    if output_format not in formatters:
        raise ValueError(f"Invalid output format: {output_format}")
    formatter_class: IFormatter = formatters[output_format]

    string = formatter_class.preamble()
    for index, chunk in enumerate(data['chunks'], 1):
        entry = formatter_class.format_chunk(chunk, index)

        if verbose:
            print(entry)

        string += entry

    with open(f"{output_path}.{output_format}", 'w', encoding='utf-8') as file:
        file.write(string)
