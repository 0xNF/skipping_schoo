import os
import sys
import argparse

import openai

from skipping_schoo import version
from skipping_schoo import download_schoo
from skipping_schoo import rip_audio
from skipping_schoo import transscribe
from skipping_schoo import summarize
from skipping_schoo import utils
from skipping_schoo.errors import SkippingSchooError

PROG = "SkippingSchoo"


__version__ = version.VERSION
__all__ = [
    "version",
    "download_schoo",
    "rip_audio",
    "transscribe",
    "summarize",
    "utils",
]


def _pipeline(url: str, overwrite: bool = False, cleanup: bool = False) -> str:
    """Runs the entire pipeline for downloading a schoo video. Prints the transcription to the terminal"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key is None or len(openai_key) == 0:
        raise SkippingSchooError(
            "No OpenAI API key set at the OPENAI_API_KEY environment variable"
        )
    else:
        openai.api_key = openai_key
    course_title = download_schoo.get_video_title(url)
    video_path = _downloadSchoo(url, overwrite=overwrite, cleanup=cleanup)
    wav_path = _ripAudio(video_path, overwrite=overwrite, cleanup=cleanup)
    transcription_path = _transcribeAudio(
        wav_path, overwrite=overwrite, cleanup=cleanup
    )
    summarize_path = _summarize(
        transcription_path, course_title, overwrite=overwrite, cleanup=cleanup
    )
    with open(summarize_path, "r", encoding=utils.ENCODING) as f:
        summary = f.read()
        print(summary)
        return summary


def _downloadSchoo(url: str, overwrite: bool = False, cleanup: bool = False) -> str:
    """Downloads an entire schoo video from a schoo [url] or class id and returns the path of the file on disk"""
    video_id = download_schoo.parse_url(url)
    m3u8 = download_schoo.get_m3u8_link(video_id)
    video_path = download_schoo.get_video(m3u8, f"{video_id}.mp4", overwrite=overwrite)
    return video_path


def _ripAudio(video_path: str, overwrite: bool = False, cleanup: bool = False) -> str:
    """Rips the audio of a file at the [video_path] into a 16khz mono wav file
    returns the path of the downloaded wav file
    """
    output_name = utils.make_output_filename(video_path, "wav")
    wav_path = rip_audio.rip(
        video_path, output_name, overwrite=overwrite, cleanup=cleanup
    )
    return wav_path


def _transcribeAudio(
    audio_path: str, overwrite: bool = False, cleanup: bool = False
) -> str:
    """Transcribes the audio file at the [audio_path] into a text file
    Returns the path of the transcribed text file
    """
    transcription_path = transscribe.transcribe(
        audio_path, overwrite=overwrite, cleanup=cleanup
    )
    return transcription_path


def _summarize(
    transcription_path: str,
    course_title: str,
    overwrite: bool = False,
    cleanup: bool = False,
) -> str:
    """Takes the transcription at [transcription_path] and summarizes it
    Returns the path of summary text file
    """
    summary_path = summarize.summarizer_file(
        transcription_path, course_title, overwrite=overwrite, cleanup=cleanup
    )
    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Runs the entire pipeline to download a schoo video, rip its audio, transcribe its contents, and provide a summary",
    )
    parser.add_argument("url", help="Schoo URL or course number to summarize")

    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="If set, overwrites every step of the process if any files from a prevous run of the same file existed",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="if set, will delete all intermediary data generated, keeping only the final summary.txt",
    )

    args = parser.parse_args()

    _pipeline(args.url, overwrite=args.overwrite, cleanup=args.cleanup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
