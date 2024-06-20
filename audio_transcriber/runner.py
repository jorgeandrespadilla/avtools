import json
from audio_transcriber.models import DiarizationConfig, TranscriptionConfig
from audio_transcriber.pipelines import transcription, diarization


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
            new_chunks.append({"speaker": current_speaker, "timestamp": chunk["timestamp"], "text": ""})
        new_chunks[-1]["timestamp"] = [new_chunks[-1]["timestamp"][0], chunk["timestamp"][1]]
        new_chunks[-1]["text"] += chunk["text"]
    return new_chunks


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
            fp.write(transcript_to_text(result, group_by_speaker=True))
    else:
        with open(output_file, "w", encoding="utf8") as fp:
            json.dump(result, fp, ensure_ascii=False)
