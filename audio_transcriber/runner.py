import json
from audio_transcriber.models import DiarizationConfig, TranscriptionConfig
from audio_transcriber.pipelines import transcription, diarization


def build_result(transcript, outputs):
    return {
        "speakers": transcript,
        "chunks": outputs["chunks"],
        "text": outputs["text"],
    }


def run(
    input_file: str,
    output_file: str,
    hf_token: str | None = None,
    device_id: str = "cuda:0", # 'cuda:{#}' or 'mps' for Mac devices
    enable_timestamps: bool = True,
):
    if hf_token and not enable_timestamps:
        raise ValueError(
            "Diarization requires timestamps to be enabled."
        )

    # Transcription
    outputs = transcription.run(TranscriptionConfig(
        input_file=input_file,
        device_id=device_id,
        enable_timestamps=enable_timestamps,
    ))

    # Diarization
    if hf_token:
        speakers_transcript = diarization.run(DiarizationConfig(
            input_file=input_file,
            device_id=device_id,
            hf_token=hf_token,
        ), outputs)
        result = build_result(speakers_transcript, outputs)
    else:
        result = build_result([], outputs)

    with open(output_file, "w", encoding="utf8") as fp:
        json.dump(result, fp, ensure_ascii=False)
