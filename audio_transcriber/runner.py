import json
from audio_transcriber.models import DiarizationConfig, TranscriptionConfig
from audio_transcriber.pipelines import transcription, diarization


def build_result(transcript, outputs):
    return {
        "speakers": transcript,
        "chunks": outputs["chunks"],
        "text": outputs["text"],
    }


def transcript_to_text(transcript: dict):
    if "speakers" in transcript:
        return "\n\n".join(
            f"{speaker['speaker']} ({speaker['timestamp'][0]}-{speaker['timestamp'][1]}):\n{speaker['text']}"
            for speaker in transcript["speakers"]
        )
    else:
        return transcript["text"]


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

    if output_file.endswith(".txt"):
        with open(output_file, "w", encoding="utf8") as fp:
            fp.write(transcript_to_text(result))
    else:
        with open(output_file, "w", encoding="utf8") as fp:
            json.dump(result, fp, ensure_ascii=False)
