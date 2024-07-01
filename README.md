# AV Tools

A collection of CLI tools for audio and video processing.

## Features

- Audio transcription and diarization
- Transcript formatting
- Video to audio conversion
- YouTube video downloader

## Prerequisites

- Python 3.11
- [FFmpeg v7 full build](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z) and add the bin folder to the PATH environment variable.

## Installation

> To use diarization feature, you must have a Hugging Face account and follow these steps:
> 1. Accept pyannote/segmentation-3.0 user conditions
> 2. Accept pyannote/speaker-diarization-3.1 user conditions
> 3. Create access token at hf.co/settings/tokens.

Install avtools using `pipx` (`pip install pipx` or `brew install pipx`):
```bash
pipx install git+https://github.com/jorgeandrespadilla/avtools.git
```

> To uninstall the package, just run `pipx uninstall avtools`.

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

## Contributing

### Development

> This project uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have it installed, follow the instructions [here](https://python-poetry.org/docs/#installation).

To work on the project, follow these steps:

1. Clone the repository
2. Install the dependencies: `poetry install --no-root`
3. Run the CLI application: `poetry run python cli.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
