import sys
from typing import Any
from pydantic import BaseModel
import requests
import torch
import numpy as np
from pyannote.audio import Pipeline
from torchaudio import functional as F
from transformers.pipelines.audio_utils import ffmpeg_read
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn, SpinnerColumn

from avtools.utils import is_url, resolve_device_type


class PipelineParams(BaseModel):
    input_file: str
    hf_token: str
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    device_id: str | None = None
    num_speakers: int | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None


def preprocess_inputs(inputs):
    if isinstance(inputs, str):
        if is_url(inputs):
            # We need to actually check for a real protocol, otherwise it's impossible to use a local file
            # like http_huggingface_co.png
            inputs = requests.get(inputs).content
        else:
            with open(inputs, "rb") as f:
                inputs = f.read()

    if isinstance(inputs, bytes):
        inputs = ffmpeg_read(inputs, 16000)

    if isinstance(inputs, dict):
        # Accepting `"array"` which is the key defined in `datasets` for better integration
        if not ("sampling_rate" in inputs and ("raw" in inputs or "array" in inputs)):
            raise ValueError(
                "When passing a dictionary to ASRDiarizePipeline, the dict needs to contain a "
                '"raw" key containing the numpy array representing the audio and a "sampling_rate" key, '
                "containing the sampling_rate associated with that array"
            )

        _inputs = inputs.pop("raw", None)
        if _inputs is None:
            # Remove path which will not be used from `datasets`.
            inputs.pop("path", None)
            _inputs = inputs.pop("array", None)
        in_sampling_rate = inputs.pop("sampling_rate")
        inputs = _inputs
        if in_sampling_rate != 16000:
            inputs = F.resample(torch.from_numpy(inputs), in_sampling_rate, 16000).numpy()

    if not isinstance(inputs, np.ndarray):
        raise ValueError(f"We expect a numpy ndarray as input, got `{type(inputs)}`")
    if len(inputs.shape) != 1:
        raise ValueError("We expect a single channel audio input for ASRDiarizePipeline")

    # diarization model expects float32 torch tensor of shape `(channels, seq_len)`
    diarizer_inputs = torch.from_numpy(inputs).float()
    diarizer_inputs = diarizer_inputs.unsqueeze(0)

    return inputs, diarizer_inputs


def diarize_audio(diarizer_inputs, diarization_pipeline, num_speakers, min_speakers, max_speakers):
    diarization = diarization_pipeline(
        {"waveform": diarizer_inputs, "sample_rate": 16000},
        num_speakers=num_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    segments = []
    for segment, track, label in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "segment": {"start": segment.start, "end": segment.end},
                "track": track,
                "label": label,
            }
        )

    # diarizer output may contain consecutive segments from the same speaker (e.g. {(0 -> 1, speaker_1), (1 -> 1.5, speaker_1), ...})
    # we combine these segments to give overall timestamps for each speaker's turn (e.g. {(0 -> 1.5, speaker_1), ...})
    new_segments = []
    prev_segment = cur_segment = segments[0]

    for i in range(1, len(segments)):
        cur_segment = segments[i]

        # check if we have changed speaker ("label")
        if cur_segment["label"] != prev_segment["label"] and i < len(segments):
            # add the start/end times for the super-segment to the new list
            new_segments.append(
                {
                    "segment": {
                        "start": prev_segment["segment"]["start"],
                        "end": cur_segment["segment"]["start"],
                    },
                    "speaker": prev_segment["label"],
                }
            )
            prev_segment = segments[i]

    # add the last segment(s) if there was no speaker change
    new_segments.append(
        {
            "segment": {
                "start": prev_segment["segment"]["start"],
                "end": cur_segment["segment"]["end"],
            },
            "speaker": prev_segment["label"],
        }
    )

    return new_segments


def post_process_segments_and_transcripts(new_segments, transcript, group_by_speaker) -> list:
    # get the end timestamps for each chunk from the ASR output
    end_timestamps = np.array(
        [
            chunk["timestamp"][-1] if chunk["timestamp"][-1] is not None else sys.float_info.max
            for chunk in transcript
        ]
    )
    segmented_preds = []

    # align the diarizer timestamps and the ASR timestamps
    for segment in new_segments:
        # get the diarizer end timestamp
        end_time = segment["segment"]["end"]
        # find the ASR end timestamp that is closest to the diarizer's end timestamp and cut the transcript to here
        upto_idx = np.argmin(np.abs(end_timestamps - end_time))

        if group_by_speaker:
            segmented_preds.append(
                {
                    "speaker": segment["speaker"],
                    "text": "".join([chunk["text"] for chunk in transcript[: upto_idx + 1]]),
                    "timestamp": (
                        transcript[0]["timestamp"][0],
                        transcript[upto_idx]["timestamp"][1],
                    ),
                }
            )
        else:
            for i in range(upto_idx + 1):
                segmented_preds.append({"speaker": segment["speaker"], **transcript[i]})

        # crop the transcripts and timestamp lists according to the latest timestamp (for faster argmin)
        transcript = transcript[upto_idx + 1 :]
        end_timestamps = end_timestamps[upto_idx + 1 :]

        if len(end_timestamps) == 0:
            break

    return segmented_preds


def run(config: PipelineParams, outputs: Any):
    device = resolve_device_type(config.device_id)
    
    diarization_pipeline = Pipeline.from_pretrained(
        checkpoint_path=config.diarization_model,
        use_auth_token=config.hf_token,
    )

    diarization_pipeline.to(torch.device(device))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(style="yellow1", pulse_style="white"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("[yellow]Segmenting...", total=None)

        inputs, diarizer_inputs = preprocess_inputs(inputs=config.input_file)

        segments = diarize_audio(
            diarizer_inputs,
            diarization_pipeline,
            config.num_speakers,
            config.min_speakers,
            config.max_speakers,
        )

        return post_process_segments_and_transcripts(
            segments, outputs["chunks"], group_by_speaker=False
        )
