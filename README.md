# Audio Transcriber

## Prerequisites

- Python 3.10 & Poetry
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
poetry run python cli.py --input <path_to_audio_file> --output <path_to_output_file>
```

To transcribe to a JSON format, use '.json' as the output file extension (recommended).

```bash
poetry run python cli.py --input <path_to_audio_file> --output <path_to_output_file>.json
```

To transcribe to a text format, use '.txt' as the output file extension.

```bash
poetry run python cli.py --input <path_to_audio_file> --output <path_to_output_file>.txt
```

### Convert Video to Audio

```bash
poetry run python video_to_audio.py <path_to_input_video_file>.mp4 -o <path_to_output_audio_file>.mp3
```

### Convert Transcripts to Different Formats

> Only available for transcripts generated in JSON format.

```bash
poetry run python transcript_conversor.py <path_to_input_json_file>.json -f vtt -o <path_to_output_file_without_extension>
```

Supported formats (`-f`):
- `txt`
- `vtt`
- `srt`

## Additional Information

- https://github.com/python-poetry/poetry/issues/7685
- https://github.com/Vaibhavs10/insanely-fast-whisper/issues/183
