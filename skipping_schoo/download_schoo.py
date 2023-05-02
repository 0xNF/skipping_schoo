# /usr/bin/python3
""" This file is responsible for downloading Schoo video files into a .mp4 onto your local machine"""
import os
import sys, subprocess
import argparse
import requests
from bs4 import BeautifulSoup
from typing import Union
import re

from skipping_schoo import utils
from skipping_schoo.errors import SkippingSchooError

PROG = "DownloadSchoo"
SCHOO_REGEX = re.compile(r"(?:https://)?schoo.jp/class/(\d+)/room")


def log(msg: str, end="\n") -> None:
    utils.log(msg, end=end, prog=PROG)


def parse_url(url: Union[str, int]) -> str:
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
            return video_id
        except:
            match = SCHOO_REGEX.match(url)
            if match is None:
                log(f"Failed to find video id in submitted URL: {url}")
                raise SkippingSchooError("No video id found in URL")
            video_id = match.group(1)
            log(f"Found video id in handed in URL. video id is {video_id}")
            return video_id
    raise SkippingSchooError("No video id found in URL")


def reconstruct_video_url(url: Union[str, int]) -> str:
    """Returns the full schoo url given either the url itself, or the class number"""
    fmt = "https://schoo.jp/class/{0}"
    if isinstance(url, int):
        return fmt.format(str(url))
    elif isinstance(url, str):
        try:
            int(url)
            return fmt.format(url)
        except:
            if url.startswith("https://schoo.jp") or url.startswith("schoo.jp"):
                return url
    raise SkippingSchooError("Not a valid Schoo URL or class number")


def get_room_html_data(video_id: str) -> BeautifulSoup:
    """Fetches the html for the room, which we use at later steps to parse out the title and m3u8 url"""
    video_url = f"{reconstruct_video_url(video_id)}/room"
    r = requests.get(video_url)
    if r.status_code != 200:
        raise SkippingSchooError(f"No such course: {video_id}")
    return BeautifulSoup(r.text, "html.parser")


def extract_m3u8_from_html(room_html: BeautifulSoup) -> str:
    """Given html data in BS form, search for the m3u8 url"""
    m3u8_re = re.compile(r"['\"]?akamai_url['\"]?:\W*(.*\.m3u8)['\"]?")
    txt = str(room_html)
    matches = [m.group(1) for m in m3u8_re.finditer(txt)]
    if len(matches) == 0:
        log(f"Failed to find m3u8 url in room html")
        raise SkippingSchooError("No m3u8 data found")
    m3u8 = matches[0]
    return m3u8


def get_m3u8_link(video_id: str, season: str = "2001") -> str:
    """Returns a URL to the .m3u8 file for downloading. Of the format 'https://video.schoo.jp/video/$season/$video_id'"""
    soup = get_room_html_data(video_id)
    return extract_m3u8_from_html(soup)
    # return f"https://video.schoo.jp/full/{season}/{video_id}.m3u8"


def get_video(m3u8_url: str, filename: str, overwrite: bool = False) -> str:
    """Uses FFMPEG to download the m3u8 file and stitch together the full video

    returns the path to the downloaded video mp4 file"""
    output_path = utils.get_output_directory_path(filename)
    os.makedirs(utils.get_output_directory_path(filename), exist_ok=True)
    full_path = os.path.join(output_path, filename)
    if not overwrite and os.path.exists(full_path):
        log(
            f"Video file already existed at {full_path}, and overwrite is set to false. Skipping download step"
        )
    else:
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
        x = subprocess.run(args, stdout=subprocess.PIPE)
        x.check_returncode()
        log(f"File downloaded to {full_path}")
    return full_path


def get_video_title(url: Union[str, int]) -> str:
    """Fetches the course url to extract the course title"""
    video_url = reconstruct_video_url(url)
    r = requests.get(video_url)
    if r.status_code != 200:
        raise SkippingSchooError(f"No such course: {url}")
    soup = BeautifulSoup(r.text, "html.parser")
    title_tag = soup.find("title")
    if title_tag == None:
        raise SkippingSchooError(
            f"No class title found in html response for course {url}"
        )
    log(f"Found tile tag, contained the following text: {title_tag.text}")
    split_on = None
    if "｜" in title_tag.text:
        split_on = "｜"
    elif "|" in title_tag.text:
        split_on = "|"
    title_text = title_tag.text.split(split_on)[0]
    log(f"Title text determined to be '{title_text}'")
    return title_text


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Downloads Schoo audio into an mp4 file using ffmpeg, taking either a url, or a video id",
    )
    parser.add_argument("url")
    parser.add_argument(
        "-t",
        "--title",
        action="store_true",
        help="Fetches the course title of the given url",
    )

    args = parser.parse_args()

    video_id = parse_url(args.url)
    if video_id is None:
        return -1
    if args.title:
        title = get_video_title(args.url)
        print(title)
        return 0
    else:
        m3u8_link = get_m3u8_link(video_id)
        get_video(m3u8_link, f"{video_id}.mp4")
        return 0


if __name__ == "__main__":
    sys.exit(main())
