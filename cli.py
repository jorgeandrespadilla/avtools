from audio_transcriber.args_parser import parse_args
from audio_transcriber.utils import file_exists, get_env, is_url
import audio_transcriber.runner as transcriber


if __name__ == "__main__":
    args = parse_args()
    hf_token = args.hf_token or get_env("HUGGING_FACE_TOKEN")

    if not is_url(args.input) and not file_exists(args.input):
        raise FileNotFoundError(f"The file '{args.input}' does not exist.")

    transcriber.run(
        input_file=args.input,
        output_file=args.output,
        # hf_token=hf_token, # TODO: Uncomment this line to use diarization
    )

    print(f"Transcription saved to '{args.output}'")
