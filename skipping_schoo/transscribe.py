# /usr/bin/python3
# -*- coding: UTF-8 -*-
""" This file is responsible for producing a transcript of a Schoo video using Whisper Large-v2 """
import codecs
import datetime
import os, sys
import subprocess
import argparse
from skipping_schoo import utils
from time import sleep
from faster_whisper import WhisperModel

PROG = "Transcribe"

MODEL_SIZE = "large-v2"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
LANGUAGE = "ja"

FMT = "[{0} -> {1}] {2}"


def log(msg: str, end="\n") -> None:
    return utils.log(msg, end=end, prog=PROG)


def get_runtime_secs(input_file: str) -> int:
    args = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_file,
    ]
    x = subprocess.run(args, stdout=subprocess.PIPE, encoding="utf8")
    x.check_returncode()
    dur_str = x.stdout.strip()
    dur_str = dur_str.split(".")[0]
    dur = int(dur_str)
    return dur


def transcribe(
    input_filename: str,
    model_size: str = MODEL_SIZE,
    device: str = DEVICE,
    compute_type: str = COMPUTE_TYPE,
    language: str = LANGUAGE,
    overwrite: bool = False,
) -> str:
    """Uses Whisper to create a transcript"""
    log(f"Loading Video File '{input_filename}'...")
    runtime_secs = get_runtime_secs(input_filename)
    log(
        f"file is {runtime_secs} seconds  / {round(runtime_secs / 60, 2) } minutes long"
    )

    output_filename = utils.make_output_filename(input_filename, "txt")
    output_path = utils.get_output_directory_path(input_filename)
    os.makedirs(utils.get_output_directory_path(input_filename), exist_ok=True)
    full_path_out = os.path.join(output_path, output_filename)

    if not overwrite and os.path.exists(full_path_out):
        log(
            f"Transcription file already existed at {full_path_out}, and overwrite is set to false. Skipping transcribe step"
        )
    else:
        log(f"Will write output to {full_path_out}")
        log(f"Loading Whisper model '{model_size}'...")
        whisper = WhisperModel(model_size, device=device, compute_type=compute_type)
        log("Whisper model loaded. Beginning transcription")
        segments, info = whisper.transcribe(input_filename, language=language)
        with open(full_path_out, "w", encoding="utf8") as f:
            for segment in segments:
                segment_start_secs = round(segment.start, 2)
                segment_end_secs = round(segment.end, 2)
                percent_done = round(segment_end_secs / runtime_secs, 2) * 100
                as_utf8 = segment.text
                log(
                    f"\r[{percent_done}%] Transcribed {segment_end_secs} seconds: {as_utf8}",
                    end="\r",
                )
                txt = FMT.format(segment_start_secs, segment_end_secs, as_utf8)
                f.write(txt)
                f.write("\n")
                f.flush()
        utils.eprint("", end="\r")
        log(f"Finished transcribing, output written to {full_path_out}")
    return full_path_out


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Produces a transcript of a .wav file",
    )
    parser.add_argument("audio_file")

    args = parser.parse_args()

    transcribe(args.audio_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
