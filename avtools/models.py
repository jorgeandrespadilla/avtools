from abc import ABC, abstractmethod
import argparse
from typing import Self
from pydantic import BaseModel, computed_field, field_validator, model_validator

from avtools.utils import format_duration


# region Base Models


class ICommandHandler(ABC):
    """Interface for command handlers."""
    
    name: str
    """Command name."""

    description: str
    """Command description."""

    @abstractmethod
    def configure_args(self, parser: argparse.ArgumentParser) -> None:
        """Configure the command line arguments for the command."""	
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        """Run the command with the given arguments."""
        pass

    def __str__(self):
        return self.name

# endregion


# region Transcription Data Models


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
