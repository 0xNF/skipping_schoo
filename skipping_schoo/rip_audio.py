# /usr/bin/python3
""" This file is responsible for splitting the audio of an mp4 file into a single 16khz mono wav file """
import datetime
import os, sys, subprocess
import argparse
from skipping_schoo import utils

PROG = "RipAudio"


def log(msg: str, end="\n") -> None:
    utils.log(msg, end=end, prog=PROG)


def rip(input_filename: str, output_filename: str) -> None:
    """Uses FFMPEG to rip audio"""

    output_path = utils.get_output_directory_path(input_filename)
    os.makedirs(utils.get_output_directory_path(input_filename), exist_ok=True)
    full_path_out = os.path.join(output_path, output_filename)

    log(f"Ripping audio for file '{input_filename}' into '{full_path_out}'")

    args = [
        "ffmpeg",
        "-i",
        input_filename,
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        full_path_out,
    ]
    subprocess.run(args, stdout=subprocess.PIPE)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Rips audio from an mp4 file into a single 16khz mono wav file",
    )
    parser.add_argument("video_file")

    args = parser.parse_args()

    output_filename = utils.make_output_filename(args.video_file, "wav")
    rip(args.video_file, output_filename)

    return 0


if __name__ == "__main__":
    sys.exit(main())
