import datetime
import os
import sys


ENCODING = "utf8"

def eprint(*msg: object, end: str = "\n") -> None:
    """Prints to stderr"""
    print(*msg, end=end, file=sys.stderr)


def log(msg: str, end="\n", prog: str = "<UNKNOWN>") -> None:
    """Logs the given message to stderr"""
    ct = datetime.datetime.now()
    s = ct.time().strftime("%I:%M:%S %p")
    eprint(f"[{s}] [{prog}] {msg}", end=end)


def get_basename_no_ext(fpath: str) -> str:
    """Returns the name of the given filepath without the extension"""
    return os.path.basename(fpath).split(".")[0]


def make_output_filename(fpath: str, extension: str) -> str:
    """basename + .extension"""
    fname = get_basename_no_ext(fpath)
    o = f"{fname}.{extension}"
    return o


def get_output_directory_path(fpath: str) -> str:
    """returns the main output directory for the file in question"""
    no_ext = get_basename_no_ext(fpath)
    output_path = os.path.join("./", no_ext)
    return output_path
