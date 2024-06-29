import json
from app.pipelines import transcription, diarization

SUPPORTED_INPUT_EXTENSIONS = [".mp3", ".wav"]
SUPPORTED_OUTPUT_EXTENSIONS = [".json", ".txt"]


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


def execute(
    input_file: str,
    output_file: str,
    language: str | None = None,
    hf_token: str | None = None,
    device_id: str = "cuda:0",  # 'cuda:{#}' or 'mps' for Mac devices
    enable_timestamps: bool = True,
):
    if hf_token and not enable_timestamps:
        raise ValueError("Diarization requires timestamps to be enabled.")

    # Transcription
    transcription_params = transcription.PipelineParams(
        input_file=input_file,
        device_id=device_id,
        enable_timestamps=enable_timestamps,
        language=language,
    )
    transcription_result = transcription.run(transcription_params)

    # Diarization
    if hf_token:
        diarization_params = diarization.PipelineParams(
            input_file=input_file,
            device_id=device_id,
            hf_token=hf_token,
        )
        diarization_result = diarization.run(diarization_params, transcription_result) # Speakers transcript
        result = build_result(diarization_result, transcription_result)
    else:
        result = build_result([], transcription_result)

    if output_file.endswith(".txt"):
        with open(output_file, "w", encoding="utf8") as fp:
            fp.write(transcript_to_text(result, group_by_speaker=True))
    else:
        with open(output_file, "w", encoding="utf8") as fp:
            json.dump(result, fp, ensure_ascii=False)
