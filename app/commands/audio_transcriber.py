import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from app.pipelines import transcription, diarization
from app.utils import FilePath, is_supported_extension, is_url, list_extensions

SUPPORTED_INPUT_EXTENSIONS = [".mp3", ".wav"]
SUPPORTED_OUTPUT_EXTENSIONS = [".json", ".txt"]


class CommandParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_file: str
    """
    Input video file path or URL. 
    If input file is not a URL, do not use this field directly, use the input_file_path property instead.
    """

    output_file: str
    """Output audio file path (do not use this field directly, use the output_file_path property instead)."""

    language: str | None = None
    """Language code to use for transcription."""

    hf_token: str | None = None
    """Hugging Face API token for diarization. If omitted, diarization will be disabled."""

    # Additional parameters
    device_id: str = "cuda:0"
    """
    Device ID to use for processing. Use 'cuda:{#}' for GPU devices or 'mps' for Mac devices.
    """

    enable_timestamps: bool = True
    """Enable timestamps in the transcription output."""

    @computed_field
    @property
    def input_file_or_url(self) -> str:
        """Get the input file path or URL as a string."""
        if is_url(self.input_file):
            return self.input_file
        return str(self.input_file_path)

    @computed_field
    @property
    def input_file_path(self) -> FilePath:
        """Get the input file path (fails if input is a URL)."""
        if is_url(self.input_file):
            raise ValueError("Cannot get file path for URL input (this should not happen).")
        return FilePath(self.input_file)

    @computed_field
    @property
    def output_file_path(self) -> FilePath:
        return FilePath(self.output_file)

    @model_validator(mode="after")
    def _validate_files(self) -> Self:
        self._validate_input_file()

        self._validate_output_file()

        if self.hf_token and not self.enable_timestamps:
            raise ValueError("Diarization requires timestamps to be enabled.")
        return self

    def _validate_input_file(self):
        if is_url(self.input_file):
            return self

        if not self.input_file_path.file_exists():
            raise FileNotFoundError(f"File not found: '{self.input_file_path.full_path}'")
        if not is_supported_extension(self.input_file_path.extension, SUPPORTED_INPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid input file format: '{self.input_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_INPUT_EXTENSIONS)}"
            )
        return self

    def _validate_output_file(self):
        if not self.output_file_path.directory_exists():
            raise FileNotFoundError(
                f"Directory not found: '{self.output_file_path.directory_path}'"
            )
        if not is_supported_extension(self.output_file_path.extension, SUPPORTED_OUTPUT_EXTENSIONS):
            raise ValueError(
                f"Invalid output file format: '{self.output_file_path.extension_without_dot.upper()}'. Supported formats: {list_extensions(SUPPORTED_OUTPUT_EXTENSIONS)}"
            )


def build_result(transcript, outputs):
    return {
        "speakers": transcript,
        "chunks": outputs["chunks"],
        "text": outputs["text"],
    }


def group_chunks_by_speaker(chunks: list[dict]) -> list[dict]:
    new_chunks = []
    current_speaker = None
    for chunk in chunks:
        if current_speaker != chunk["speaker"]:
            current_speaker = chunk["speaker"]
            new_chunks.append(
                {"speaker": current_speaker, "timestamp": chunk["timestamp"], "text": ""}
            )
        new_chunks[-1]["timestamp"] = [new_chunks[-1]["timestamp"][0], chunk["timestamp"][1]]
        new_chunks[-1]["text"] += chunk["text"]
    return new_chunks


# TODO: Deprecate this format and move it to the transcript formatter script
def transcript_to_text(transcript: dict, group_by_speaker: bool = False) -> str:
    if "speakers" in transcript:
        if group_by_speaker:
            transcript["speakers"] = group_chunks_by_speaker(transcript["speakers"])
        timestamp_parser = lambda x: f"{x[0]}s - {x[1]}s"  # noqa: E731
        return "\n\n".join(
            f"{speaker['speaker']} ({timestamp_parser(speaker['timestamp'])}):\n{speaker['text']}"
            for speaker in transcript["speakers"]
        )
    else:
        return transcript["text"]


def execute(params: CommandParams) -> None:
    # Transcription
    transcription_params = transcription.PipelineParams(
        input_file=params.input_file_or_url,
        device_id=params.device_id,
        enable_timestamps=params.enable_timestamps,
        language=params.language,
    )
    transcription_result = transcription.run(transcription_params)

    # Diarization
    if params.hf_token:
        diarization_params = diarization.PipelineParams(
            input_file=params.input_file_or_url,
            device_id=params.device_id,
            hf_token=params.hf_token,
        )
        diarization_result = diarization.run(
            diarization_params, transcription_result
        )  # Speakers transcript
        result = build_result(diarization_result, transcription_result)
    else:
        result = build_result([], transcription_result)

    if params.output_file_path.extension == ".txt":
        with open(params.output_file_path.full_path, "w", encoding="utf8") as fp:
            fp.write(transcript_to_text(result, group_by_speaker=True))
    else:
        with open(params.output_file_path.full_path, "w", encoding="utf8") as fp:
            json.dump(result, fp, ensure_ascii=False)
