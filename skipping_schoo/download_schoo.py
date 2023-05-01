# /usr/bin/python3
""" This file is responsible for downloading Schoo video files into a .mp4 onto your local machine"""
import datetime
import os
import sys, subprocess
import argparse
from typing import Union
import re
from skipping_schoo import utils

PROG = "DownloadSchoo"
SCHOO_REGEX = re.compile(r"(?:https://)?schoo.jp/class/(\d+)/room")


def log(msg: str, end="\n") -> None:
    utils.log(msg, end=end, prog=PROG)


def parse_url(url: Union[str, int]) -> Union[str, None]:
    """Takes something that may resemble a Schoo URL and turns it into the likely video id"""
    video_id = None
    if isinstance(url, int):
        video_id = str(url)
        log(f"Given number for extracting video id. Video id is {video_id}")
    elif isinstance(url, str):
        try:
            int(url)
            video_id = url
            log(f"Given stringified int. Returning as-is:{video_id}")
        except:
            match = SCHOO_REGEX.match(url)
            if match is None:
                log(f"Failed to find video id in submitted URL: {url}")
                return video_id
            video_id = match.group(1)
            log(f"Found video id in handed in URL. video id is {video_id}")
            return video_id
    return video_id


def get_m3u8_link(video_id: str, season: str = "2001") -> str:
    """Returns a URL to the .m3u8 file for downloading. Of the format 'https://video.schoo.jp/video/$season/$video_id'"""
    return f"https://video.schoo.jp/full/{season}/{video_id}.m3u8"


def get_video(m3u8_url: str, filename: str):
    """Uses FFMPEG to download the m3u8 file and stitch together the full video"""
    output_path = utils.get_output_directory_path(filename)
    os.makedirs(utils.get_output_directory_path(filename), exist_ok=True)
    full_path = os.path.join(output_path, filename)
    args = [
        "ffmpeg",
        "-i",
        m3u8_url,
        "-bsf:a",
        "aac_adtstoasc",
        "-vcodec",
        "copy",
        "-c",
        "copy",
        "-crf",
        "50",
        full_path,
    ]
    subprocess.run(args, stdout=subprocess.PIPE)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Downloads Schoo audio into an mp4 file using ffmpeg, taking either a url, or a video id",
    )
    parser.add_argument("url")

    args = parser.parse_args()

    video_id = parse_url(args.url)
    if video_id is None:
        return -1
    m3u8_link = get_m3u8_link(video_id)
    get_video(m3u8_link, f"{video_id}.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
