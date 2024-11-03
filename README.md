<div align="center">
  <img src="assets/hero.jpeg" alt="AV Tools" width="240" style="border-radius: 2rem;" />
  <h1 align="center">AV Tools</h1>
  <p align="center">
    A collection of CLI tools for audio and video processing.
  </p>
</div>

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

`avtools` can be installed using `pipx`. If you don't have `pipx` installed, you can install it using `pip` (`pip install pipx` and `python -m pipx ensurepath`) or `brew` (`brew install pipx` and `pipx ensurepath`).

To install the package using `pipx`, run the following command:
```bash
pipx install git+https://github.com/jorgeandrespadilla/avtools.git
```

To upgrade the package, run the following command:
```bash
pipx upgrade avtools
```

## Usage

```bash
avtools <command> [options]
```

For more information on the available commands, use the `--help` argument:

```bash
avtools --help
```

### Transcribe

```bash
avtools transcribe -i <path_to_audio_file>.mp3 -o <path_to_output_file>.json
```

> To use diarization feature, add the `--hf-token` argument with the access token. We do not recommended to use this feature for large audio files.

### Convert Video to Audio

```bash
avtools video-audio -i <path_to_input_video_file>.mp4 -o <path_to_output_audio_file>.mp3
```

### Convert Transcripts to Different Formats

> Only available for transcripts generated in JSON format.

To convert a JSON transcript to a subtitle file or plain text file, use the following command:

```bash
avtools format -i <path_to_input_json_file>.json -o <path_to_output_file>.srt
```

Supported output formats:
- `srt`
- `txt`
- `vtt`

### Download YouTube Video

```bash
avtools youtube-download -u <youtube_video_url> -o <path_to_output_file>.mp4
```

To download the video transcript, add the `--transcript` argument with the language code (e.g. `en` for English).

```bash
avtools youtube-download -u <youtube_video_url> -o <path_to_output_file>.mp4 --transcript=<language_code>
```

## Experimental Features

**How to use Flash-Attention with `avtools` transcribe command?**

Install it via `pipx runpip avtools install flash-attn --no-build-isolation`.

> We only recommend using Flash-Attention if your GPU supports it.

## Contributing

### Development

See the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information on how to contribute to this project.

### Additional Information

The following resources may be helpful when solving issues related to PyTorch package installation with Poetry:
- https://github.com/python-poetry/poetry/issues/7685
- https://github.com/Vaibhavs10/insanely-fast-whisper/issues/183
- https://github.com/python-poetry/poetry/issues/2415

Due to the way PyTorch is built, the source URLs have to be hard-coded in the `pyproject.toml` file to avoid installation issues (to support new Python versions, we should add more URLs to the `torch` packages). This is a workaround to avoid issues when working with private repositories.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
