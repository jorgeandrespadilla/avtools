# AV Tools

A collection of CLI tools for audio and video processing.

## Features

- Audio transcription and diarization
- Transcript formatting
- Video to audio conversion
- YouTube video downloader

## Prerequisites

- Python 3.11 & Poetry
- (Optional, only required for video conversion) [FFmpeg v7 full build](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z) and add the bin folder to the PATH environment variable.

## Description

This project is an AI powered audio transcriber, which is based on the [insanely-fast-whisper](https://github.com/Vaibhavs10/insanely-fast-whisper) implementation.

## Installation

> To use diarization feature, you must have a Hugging Face account and follow these steps:
> 1. Accept pyannote/segmentation-3.0 user conditions
> 2. Accept pyannote/speaker-diarization-3.1 user conditions
> 3. Create access token at hf.co/settings/tokens.

1. Clone the repository
2. Install the dependencies: `poetry install`
3. Run the CLI application: `poetry run python cli.py`

## Usage

### Transcribe

```bash
poetry run python audio_transcriber.py --input <path_to_audio_file> --output <path_to_output_file>
```

> To use diarization feature, add the `--hf-token` argument with the access token. We do not recommended to use this feature for large audio files.

```bash

To transcribe to a JSON format, use '.json' as the output file extension (recommended).

```bash
poetry run python audio_transcriber.py --input <path_to_audio_file> --output <path_to_output_file>.json
```

To transcribe to a text format, use '.txt' as the output file extension.

```bash
poetry run python audio_transcriber.py --input <path_to_audio_file> --output <path_to_output_file>.txt
```

### Convert Video to Audio

```bash
poetry run python video_to_audio_converter.py -i <path_to_input_video_file>.mp4 -o <path_to_output_audio_file>.mp3
```

### Convert Transcripts to Different Formats

> Only available for transcripts generated in JSON format.

To convert a JSON transcript to a subtitle file or plain text file, use the following command:

```bash
poetry run python transcript_formatter.py -i <path_to_input_json_file>.json -o <path_to_output_file>.vtt
```

Supported output formats:
- `srt`
- `txt`
- `vtt`

### Download YouTube Video

```bash
poetry run python youtube_video_downloader.py -u <youtube_video_url> -o <path_to_output_file>.mp4
```

For more information on the available options, run the following command:

```bash
poetry run python youtube_video_downloader.py --help
```

## Summarize Videos

```bash
poetry run python video_summarizer.py \
    -v <path_to_input_video_file>.mp4 \
    -t <path_to_output_transcript_file>.vtt \
    -o <path_to_output_directory>
    --openai_key <openai_api_key>
```

For more information on the available options, run the following command:

```bash
poetry run python video_summarizer.py --help
```

## Development

### Testing

To run manual tests, use the following command:

```bash
poetry run python -m tests.utils._your_test_file_
```

> All manual tests are located in files prefixed with an underscore (eg. `_test_file_path`).	

## Additional Information

- https://github.com/python-poetry/poetry/issues/7685
- https://github.com/Vaibhavs10/insanely-fast-whisper/issues/183
- https://pybit.es/articles/how-to-package-and-deploy-cli-apps/