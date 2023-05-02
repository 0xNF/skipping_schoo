# /usr/bin/python3
""" This file is responsible for splitting the audio of an mp4 file into a single 16khz mono wav file """
import datetime
import os, sys, subprocess
import argparse
from skipping_schoo import utils

PROG = "RipAudio"


def log(msg: str, end="\n") -> None:
    utils.log(msg, end=end, prog=PROG)


def rip(
    input_filename: str,
    output_filename: str,
    overwrite: bool = False,
    cleanup: bool = False,
) -> str:
    """Uses FFMPEG to rip audio
    returns the path of the output wav file
    """

    output_path = utils.get_output_directory_path(input_filename)
    os.makedirs(utils.get_output_directory_path(input_filename), exist_ok=True)
    full_path_out = os.path.join(output_path, output_filename)

    if not overwrite and os.path.exists(full_path_out):
        log(
            f"Audio file already existed at {full_path_out}, and overwrite is set to false. Skipping rip step"
        )
    else:
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
        x = subprocess.run(args, stdout=subprocess.PIPE)
        x.check_returncode()
    if cleanup:
        log(f"Cleanup set to true, deleting input video at {input_filename}")
        os.unlink(input_filename)
    return full_path_out


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Rips audio from an mp4 file into a single 16khz mono wav file",
    )
    parser.add_argument("video_file")
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="if set, will overwrite any existing files on disk related to previous extraction attempts on the input video",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="if set, will delete the source video after ripping the audio",
    )

    args = parser.parse_args()

    output_filename = utils.make_output_filename(args.video_file, "wav")
    rip(
        args.video_file,
        output_filename,
        overwrite=args.overwrite,
        cleanup=args.cleanup,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
