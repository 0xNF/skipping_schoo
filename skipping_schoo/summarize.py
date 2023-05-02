# /usr/bin/python3
""" This file is responsible for sending transcript data to ChatGPT to get a summary of the contents"""
from ast import List
import datetime
import math
import os
import sys, subprocess
import argparse
import time
from typing import Union
import re
import openai
from transformers import AutoTokenizer
import torch
from openai.error import RateLimitError
from skipping_schoo import utils
import shutil

PROG = "Summarize"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 100

MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.5
MAX_TOKENS = CHUNK_SIZE
TOP_P = 1
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0

TOKENIZER = AutoTokenizer.from_pretrained("gpt2")


def log(msg: str, end="\n") -> None:
    utils.log(msg, end=end, prog=PROG)


def count_tokens_file(filename: str) -> int:
    """Runs a local tokenizer that roughly matches OpenAI's gpt3 and returns the total tokens in a given text from a filename"""
    with open(filename, "r", encoding=utils.ENCODING) as f:
        text = f.read()
        return count_tokens_text(text)


def count_tokens_text(text: str) -> int:
    """Runs a local tokenizer that roughly matches OpenAI's gpt3 and returns the total tokens for the given text"""
    input_ids = torch.tensor(TOKENIZER.encode(text)).unsqueeze(0)
    num_tokens = input_ids.shape[1]
    return num_tokens


def break_up_to_chunks_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[list[int]]:
    """Given some text, breaks up that file into individual lists containing a token count that GPT-3 can accept in a single request"""
    tokens = TOKENIZER.encode(text)
    num_tokens = len(tokens)

    chunks = []
    for i in range(0, num_tokens, chunk_size - overlap):
        chunk = tokens[i : i + chunk_size]
        chunks.append(chunk)
    return chunks


def break_up_to_chunks_file(
    filename: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[list[int]]:
    """Given a file containing text, breaks up that file into individual lists containing a token count that GPT-3 can accept in a single request"""
    with open(filename, "r", encoding=utils.ENCODING) as f:
        text = f.read()
        return break_up_to_chunks_text(text, chunk_size, overlap)


def write_chunks_to_files(
    filename: str, overwrite: bool = True, output_path: str = "./"
) -> list[list[int]]:
    """Given a filename containing some tokens, split the file into individual lists of tokens that GPT-3 can access in a single request.
    Writes these lists back out to disk in numbered order.
    Returns the list of chunks in memory
    """
    os.makedirs(output_path, exist_ok=True)
    chunks = break_up_to_chunks_file(filename)
    for i, chunk in enumerate(chunks):
        fname = _get_chunked_filename(filename, i)
        full_path = os.path.join(output_path, fname)
        if os.path.isfile(full_path) and not overwrite:
            log(f"\rSkipping writing Chunk {i}, file already exists", end="\r")
            continue
        log(f"\rWriting Chunk {i}: {len(chunk)} tokens", end="\r")
        retokenized = TOKENIZER.decode(chunk)
        with open(full_path, "w", encoding=utils.ENCODING) as f:
            f.write(retokenized)
    log("Finished writing chunked token files")
    return chunks


def _stitch_summaries(summaries: list[str]) -> str:
    return "\n".join(summaries)


def summarizer_file(
    filename: str, course_title: str, overwrite: bool = False, cleanup: bool = False
) -> str:
    base_dir = utils.get_output_directory_path(filename)
    chunk_path = os.path.join(base_dir, "chunks")
    summary_path = os.path.join(base_dir, "summaries")
    chunks = write_chunks_to_files(
        filename, overwrite=overwrite, output_path=chunk_path
    )

    summaries: list[str] = []
    if len(chunks) > 1:
        summaries = send_summary_prompts(
            chunks,
            course_title,
            filename,
            overwrite=overwrite,
            output_path=summary_path,
        )
    elif len(chunks) == 1:
        log(
            "chunks was length==1, meaning that there's no need to do a meta-summary. We can instead move on to summarizing the raw input"
        )
        summaries = [TOKENIZER.decode(x) for x in chunks]
    else:
        log(
            "chunks was length==0, which is an error. There is nothing to summarize. Returning blank."
        )
        return ""
    summary = summary_of_summaries(filename, summaries, course_title)
    if cleanup:
        log(f"Cleanup set to true, deleting snippet and summary collections")
        shutil.rmtree(chunk_path, ignore_errors=True)
        shutil.rmtree(summary_path, ignore_errors=True)
    return summary


def recurse_summary(
    prompt: str,
    chunk_idx: int,
    course_title: str,
    filename: str,
    output_path: str = "./",
) -> str:
    prompt = prompt.strip()
    if len(prompt) == 0:
        log(
            "Prompt was empty, which is an error. Returning nothing and not sending anything out to OpenAI"
        )
        return ""
    try:
        response_text = _send_openai_request(
            prompt,
            MODEL,
            TEMPERATURE,
            MAX_TOKENS,
            TOP_P,
            FREQUENCY_PENALTY,
            PRESENCE_PENALTY,
        )
        fname = _get_summarized_filename(filename, chunk_idx)
        full_path = os.path.join(output_path, fname)
        with open(full_path, "w", encoding=utils.ENCODING) as f:
            f.write(response_text)
        return response_text
    except RateLimitError as rle:
        _extract_and_wait_on_rate_limit(rle)
        # recurse back in, so we can catch new rate limit errors from the rate limited execution
        return recurse_summary(prompt, chunk_idx, course_title, filename, output_path)


def _extract_and_wait_on_rate_limit(rle: RateLimitError):
    wait_for = 60
    log(str(rle))
    try:
        time_remaining_str = rle.headers["x-ratelimit-reset-requests"]
        wait_for = _parse_time_remaining(time_remaining_str)
    except:
        log(
            "Tried to get time remaining from Rate Limit Error headers but failed. Waiting for 60 seconds as a fallback"
        )
    while wait_for > 0:
        time.sleep(1)
        log(
            f"\rWaiting {wait_for} seconds before re-running latest command",
            end="\r",
        )
        wait_for -= 1


def send_summary_prompts(
    chunks: list[list[int]],
    course_title: str,
    filename: str,
    overwrite: bool = True,
    output_path: str = "./",
) -> list[str]:
    """Given a list chunked tokens, submits each list to OpenAI individually and returns a summary of the contents

    Writes these summaries out to a '/summaries' folder

    Returns the in-memory list of summaries
    """
    os.makedirs(output_path, exist_ok=True)
    prompt_response: list[str] = []

    initial_prompt = 'The following is snippet {0} of {1}, of a Japanese language transcript of an online course titled "{2}". Summarize it. Pay attention to any especially important parts, and include those in your summary. Do not include the course title in your summary.'

    for i, chunk in enumerate(chunks):
        full_path = os.path.join(output_path, _get_summarized_filename(filename, i))
        if os.path.exists(full_path) and not overwrite:
            log(f"Skipping sending chunk {i} for summary, already on disk")
            with open(full_path, "r", encoding=utils.ENCODING) as f:
                summarized_on_disk = f.read()
                prompt_response.append(summarized_on_disk)
            continue
        log(
            f"Sending out chunk {i} ({math.ceil(((i+1) / len(chunks))*100)}%) to OpenAI"
        )
        prompt_request = initial_prompt.format(i + 1, len(chunks), course_title)

        res = recurse_summary(prompt_request, i, course_title, filename, output_path)
        prompt_response.append(res)

    return prompt_response


def summary_of_summaries(filename: str, summaries: list[str], course_title: str) -> str:
    """Stitches each of the summaries together into one meta-summary and requests OpenAI summarize that instead
    returns the path to the written output summary
    """
    stitched = _stitch_summaries(summaries).strip()
    if len(stitched) == 0:
        log(
            "Handed empty string to summarize, which is an error. Returning blank, and not sending anything to OpenAI"
        )
        return ""
    try:
        prompt = 'The following is a list of summaries of an online course titled "{0}".  Extract between 10 to 20 bullet points of important, interesting, useful, or notable information:'.format(
            course_title
        )
        log("Sending request for summary of sumaries out to OpenAI")
        res = _send_openai_request(prompt)
        output_path = os.path.join(
            utils.get_output_directory_path(filename),
            _get_final_resposne_filename(filename),
        )
        log(
            f"Received final summary response. Response will be written to {output_path}"
        )
        with open(output_path, "w", encoding=utils.ENCODING) as f:
            f.write(res)
        return output_path
    except RateLimitError as rle:
        _extract_and_wait_on_rate_limit(rle)
        return summary_of_summaries(filename, summaries, course_title)


def _parse_time_remaining(remaining: Union[str, int, float]) -> int:
    """Given a string in the form of 'xx.yyys" returns the time remaining in integer seconds (rounded up)"""
    default = 60
    if isinstance(remaining, int):
        return remaining
    elif isinstance(remaining, float):
        return math.ceil(remaining)
    elif isinstance(remaining, str):
        try:
            s2 = [c for c in remaining if c.isdigit() or c == "."]
            last = remaining[-1].lower()
            s3 = "".join(s2)
            i = math.ceil(float(s3))
            if last == "s":
                return i
            elif last == "m":
                return i * 60
            elif last == "h":
                return i * 60 * 60
        except Exception as e:
            log(
                f"Encountered a conversion error while trying to determine rate limit time remaining on {remaining}. Got {e}. Returning '60 seconds' default"
            )
    return default


def _send_openai_request(
    prompt_request: str,
    model: str = MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    top_p: float = TOP_P,
    frequency_penalty: float = FREQUENCY_PENALTY,
    presence_penalty: float = PRESENCE_PENALTY,
) -> str:
    messages = [{"role": "system", "content": "This is text summarization."}]
    messages.append({"role": "user", "content": prompt_request})
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    response_text = response["choices"][0]["message"]["content"].strip()
    return response_text


def set_openai_key(key: str) -> None:
    os.environ["OPENAI_API_KEY"] = key


def _get_chunked_filename(filename: str, chunk_number: int) -> str:
    base = utils.get_basename_no_ext(filename)
    return f"{base}_{chunk_number}.txt"


def _get_summarized_filename(filename: str, chunk_number: int) -> str:
    base = utils.get_basename_no_ext(filename)
    return f"{base}_{chunk_number}_summary.txt"


def _get_final_resposne_filename(filename: str) -> str:
    base = utils.get_basename_no_ext(filename)
    return f"{base}_summary.txt"


def main() -> int:
    openai.api_key = os.getenv("OPENAI_API_KEY")

    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Chunks and summarizes a transcript",
    )
    parser.add_argument("transcript")
    parser.add_argument("title")
    parser.add_argument(
        "-b",
        "--block",
        action="store_true",
        help="Produces n textfiles where each file is one chunk of the full input text",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="If set, overwrites all files that may be on disk and requests a brand new set of chunked summaries from OpenAI. Keep unset if you want to be able to recover from a crash",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        help="if set, will delete the summary snippets after processing the final summary of summaries",
    )

    args = parser.parse_args()

    if args.chunk:
        write_chunks_to_files(args.transcript)
    else:
        summarizer_file(args.transcript, args.title, overwrite=args.overwrite, cleanup=args.cleanup)

    return 0


if __name__ == "__main__":
    sys.exit(main())
