import json
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator
from app.pipelines import transcription, diarization
from app.utils import FilePath, format_duration, is_supported_extension, is_url, list_extensions

SUPPORTED_INPUT_EXTENSIONS = [".mp3", ".wav"]
SUPPORTED_OUTPUT_EXTENSIONS = [".json", ".txt"]


# region Parameters


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


# endregion


# region Data Models


class TranscriptionChunkData(BaseModel):
    """Transcription data for a chunk of speech."""

    timestamp: list[float]
    """Start and end timestamps of the speaker's speech (in seconds)."""

    text: str
    """Transcribed text."""

    @computed_field
    @property
    def start_time(self) -> float:
        """Start time of the chunk (in seconds)."""
        return self.timestamp[0]

    @computed_field
    @property
    def end_time(self) -> float:
        """End time of the chunk (in seconds)."""
        return self.timestamp[1]

    @field_validator("text", mode="before")
    @classmethod
    def trim_spaces(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @model_validator(mode="after")
    def _validate_timestamp(self) -> Self:
        if len(self.timestamp) != 2:
            raise ValueError(
                f"Invalid timestamp: {self.timestamp}. Expected 2 values (start and end times)."
            )
        if self.timestamp[0] < 0:
            raise ValueError(f"Invalid start time: {self.timestamp[0]}")
        if self.timestamp[1] < 0:
            raise ValueError(f"Invalid end time: {self.timestamp[1]}")
        if self.timestamp[1] < self.timestamp[0]:
            raise ValueError(f"End time is less than start time: {self.timestamp}")
        return self

    def format_timestamp(self) -> str:
        return f"{format_duration(self.start_time)} --> {format_duration(self.end_time)}"

    def __str__(self):
        return f"({self.format_timestamp()})\n{self.text}"


class TranscriptionSpeakerData(TranscriptionChunkData):
    """Transcription data for a speaker."""

    speaker: str
    """Speaker identifier."""

    def __str__(self):
        return f"{self.speaker}\n({self.format_timestamp()})\n{self.text}"


class TranscriptionResultData(BaseModel):
    """Transcription result data."""

    speakers: list[TranscriptionSpeakerData]
    """Speaker chunks."""

    chunks: list[TranscriptionChunkData]
    """Transcription chunks."""

    text: str
    """Full transcribed text."""

    @field_validator("text", mode="before")
    @classmethod
    def trim_spaces(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    def group_by_speaker(self) -> "TranscriptionResultData":
        """Group chunks by speaker. If speaker data is not available, return the original result."""

        if not self.speakers:
            return self  # Unable to group chunks without speaker data

        new_speaker_chunks: list[TranscriptionSpeakerData] = []
        current_speaker = None
        for speaker_chunk in self.speakers:
            if current_speaker != speaker_chunk.speaker:
                current_speaker = speaker_chunk.speaker
                new_speaker_chunks.append(
                    TranscriptionSpeakerData(
                        speaker=current_speaker,
                        timestamp=[*speaker_chunk.timestamp],
                        text="",
                    )
                )
            new_speaker_chunks[-1].timestamp = [
                new_speaker_chunks[-1].start_time,
                speaker_chunk.end_time,
            ]
            if new_speaker_chunks[-1].text:
                new_speaker_chunks[-1].text += f" {speaker_chunk.text}"
            else:
                new_speaker_chunks[-1].text = speaker_chunk.text
        return TranscriptionResultData(
            speakers=new_speaker_chunks,
            chunks=self.chunks,
            text=self.text,
        )


# endregion


def _build_result(diarization_chunks: list, outputs) -> TranscriptionResultData:
    """Build the final transcription result using the output of the diarization and transcription pipelines."""
    return TranscriptionResultData(
        speakers=diarization_chunks,
        chunks=outputs["chunks"],
        text=outputs["text"],
    )


# TODO: Deprecate this format and move it to the transcript formatter script.
def _transcript_to_text(transcript: TranscriptionResultData) -> str:
    """
    Convert the transcription result to a text format.

    Remarks
    ----
    - If speaker data is available, use the speaker format. Otherwise, use the chunk format.
    """

    if transcript.speakers:
        return "\n\n".join([str(speaker) for speaker in transcript.speakers])
    return "\n\n".join([str(chunk) for chunk in transcript.chunks])


def execute(params: CommandParams) -> None:
    """Execute the audio transcription command."""

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
        result = _build_result(diarization_result, transcription_result)
    else:
        result = _build_result([], transcription_result)

    if params.output_file_path.extension == ".txt":
        with open(params.output_file_path.full_path, "w", encoding="utf8") as fp:
            fp.write(_transcript_to_text(result.group_by_speaker()))
    else:
        with open(params.output_file_path.full_path, "w", encoding="utf8") as fp:
            json.dump(result.model_dump(), fp, ensure_ascii=False)
