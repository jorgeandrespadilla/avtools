import argparse

from audio_transcriber.formatter import format_transcript


def main():
    parser = argparse.ArgumentParser(description="Convert transcript in JSON format to a subtitle file or plain text.")                                 
    parser.add_argument("input_file", help="Input JSON file path")
    parser.add_argument("-f", "--output_format", default="all", help="Format of the output file (default: srt)", choices=["txt", "vtt", "srt"])
    parser.add_argument("-o", "--output_file", default=".", help="File where the output will be saved (an extension will be added to the file name based on the output format)")
    parser.add_argument("--verbose", action="store_true", help="Print each VTT entry as it's added")

    args = parser.parse_args()
    format_transcript(args.input_file, args.output_format, args.output_file, args.verbose)

if __name__ == "__main__":
    # Example Usage:
    # python conversor.py output.json -f vtt -o /tmp/my/output/file
    main()