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

## Installation

> To use diarization feature, you must have a Hugging Face account and follow these steps:
> 1. Accept pyannote/segmentation-3.0 user conditions
> 2. Accept pyannote/speaker-diarization-3.1 user conditions
> 3. Create access token at hf.co/settings/tokens.

1. Clone the repository
2. Install the dependencies: `poetry install`
3. Run the CLI application: `poetry run python cli.py`

## Usage

```bash
poetry run python cli.py
```

For more information on the available commands, use the `--help` argument:

```bash
poetry run python cli.py --help
```

### Transcribe

```bash
poetry run python cli.py transcribe --i <path_to_audio_file>.mp3 --o <path_to_output_file>.json
```

> To use diarization feature, add the `--hf-token` argument with the access token. We do not recommended to use this feature for large audio files.

### Convert Video to Audio

```bash
poetry run python cli.py video-audio -i <path_to_input_video_file>.mp4 -o <path_to_output_audio_file>.mp3
```

### Convert Transcripts to Different Formats

> Only available for transcripts generated in JSON format.

To convert a JSON transcript to a subtitle file or plain text file, use the following command:

```bash
poetry run python cli.py format --i <path_to_input_json_file>.json --o <path_to_output_file>.srt
```

Supported output formats:
- `srt`
- `txt`
- `vtt`

### Download YouTube Video

```bash
poetry run python cli.py youtube-download -u <youtube_video_url> -o <path_to_output_file>.mp4
```

To download the video transcript, add the `--transcript` argument with the language code (e.g. `en` for English).

```bash
poetry run python cli.py youtube-download -u <youtube_video_url> -o <path_to_output_file>.mp4 --transcript=<language_code>
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
