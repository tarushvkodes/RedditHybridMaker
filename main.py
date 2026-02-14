#!/usr/bin/env python
import argparse
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from os import name
from pathlib import Path
from subprocess import Popen
from typing import NoReturn

from prawcore import ResponseException

from reddit.subreddit import get_subreddit_threads
from utils import settings
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step, print_substep
from utils.ffmpeg_install import ffmpeg_install
from utils.id import id
from utils.version import checkversion

__VERSION__ = "3.3.2-local"


def _configure_unicode_output() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def _print_banner() -> None:
    print("\n=== Reddit Video Maker Bot (Hybrid) ===\n")
    print_markdown(
        "### Docs: https://reddit-video-maker-bot.netlify.app/ | GitHub: https://github.com/elebumm/RedditVideoMakerBot"
    )


def _ordinal(n: int) -> str:
    return "th" if 11 <= (n % 100) <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--check", action="store_true", help="Run environment/config checks only")
    parser.add_argument("--times", type=int, help="Override config times_to_run for this run")
    parser.add_argument("--subreddit", type=str, help="Override config subreddit (e.g., Sat+SAT_Math)")
    return parser.parse_args()


def _preflight() -> None:
    missing = []
    for mod in ("moviepy", "playwright", "spacy", "boto3", "praw", "toml"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    if missing:
        print_substep(
            f"Missing modules: {', '.join(missing)}. Install requirements before running.",
            style="bold red",
        )
        raise SystemExit(1)


def _apply_runtime_overrides(args: argparse.Namespace) -> None:
    if args.times is not None:
        if args.times < 1:
            print_substep("--times must be >= 1", style="bold red")
            raise SystemExit(1)
        settings.config["settings"]["times_to_run"] = args.times
        print_substep(f"Override: times_to_run = {args.times}", style="bold blue")

    if args.subreddit:
        settings.config["reddit"]["thread"]["subreddit"] = args.subreddit.strip()
        print_substep(
            f"Override: subreddit = {settings.config['reddit']['thread']['subreddit']}",
            style="bold blue",
        )


def main(POST_ID=None) -> None:
    # Lazy imports reduce startup failures and allow --check mode.
    from video_creation.background import (
        chop_background,
        download_background_audio,
        download_background_video,
        get_background_config,
    )
    from video_creation.final_video import make_final_video
    from video_creation.screenshot_downloader import get_screenshots_of_reddit_posts
    from video_creation.voices import save_text_to_mp3

    global redditid, reddit_object
    reddit_object = get_subreddit_threads(POST_ID)
    if reddit_object is None:
        print_step("No suitable posts found. Skipping this iteration.")
        return

    redditid = id(reddit_object)

    # Parallelize screenshot capture with TTS in story mode to reduce wall-clock time.
    # (Safe here because storymode visuals do not depend on final comment count.)
    screenshot_future = None
    executor = None
    if settings.config["settings"].get("storymode", False) and not settings.config["settings"].get("hybrid_mode", False):
        executor = ThreadPoolExecutor(max_workers=1)
        estimated_comments = len(reddit_object.get("comments", []))
        screenshot_future = executor.submit(
            get_screenshots_of_reddit_posts, reddit_object, estimated_comments
        )

    length, number_of_comments = save_text_to_mp3(reddit_object)
    length = math.ceil(length)

    if screenshot_future is not None:
        screenshot_future.result()
        executor.shutdown(wait=True)
    else:
        get_screenshots_of_reddit_posts(reddit_object, number_of_comments)

    bg_config = {
        "video": get_background_config("video"),
        "audio": get_background_config("audio"),
    }
    download_background_video(bg_config["video"])
    download_background_audio(bg_config["audio"])
    chop_background(bg_config, length, reddit_object)
    make_final_video(number_of_comments, length, reddit_object, bg_config)


def run_many(times: int) -> None:
    for x in range(1, times + 1):
        print_step(f"on the {x}{_ordinal(x)} iteration of {times}")
        main()
        Popen("cls" if name == "nt" else "clear", shell=True).wait()


def shutdown() -> NoReturn:
    if "redditid" in globals():
        print_markdown("## Clearing temp files")
        cleanup(redditid)

    print("Exiting...")
    sys.exit()


if __name__ == "__main__":
    _configure_unicode_output()
    _print_banner()
    checkversion(__VERSION__)
    args = _parse_args()

    if sys.version_info.major != 3 or sys.version_info.minor < 10:
        print("This program requires Python 3.10+ (3.10, 3.11, 3.12, 3.13 tested).")
        sys.exit()

    ffmpeg_install()
    directory = Path().absolute()
    config = settings.check_toml(
        f"{directory}/utils/.config.template.toml", f"{directory}/config.toml"
    )
    config is False and sys.exit()

    _apply_runtime_overrides(args)
    _preflight()

    if args.check:
        print_substep("Preflight OK. Exiting because --check was passed.", style="bold green")
        sys.exit(0)

    if (
        not settings.config["settings"]["tts"]["tiktok_sessionid"]
        or settings.config["settings"]["tts"]["tiktok_sessionid"] == ""
    ) and config["settings"]["tts"]["voice_choice"] == "tiktok":
        print_substep(
            "TikTok voice requires a sessionid! Check docs for how to obtain one.",
            "bold red",
        )
        sys.exit()

    try:
        if config["reddit"]["thread"]["post_id"]:
            post_ids = config["reddit"]["thread"]["post_id"].split("+")
            for index, post_id in enumerate(post_ids, start=1):
                print_step(f"on the {index}{_ordinal(index)} post of {len(post_ids)}")
                main(post_id)
                Popen("cls" if name == "nt" else "clear", shell=True).wait()
        elif config["settings"]["times_to_run"]:
            run_many(int(config["settings"]["times_to_run"]))
        else:
            main()
    except KeyboardInterrupt:
        shutdown()
    except ResponseException:
        print_markdown("## Invalid credentials")
        print_markdown("Please check your credentials in config.toml")
        shutdown()
    except Exception as err:
        config["settings"]["tts"]["tiktok_sessionid"] = "REDACTED"
        config["settings"]["tts"]["elevenlabs_api_key"] = "REDACTED"
        print_step(
            f"Sorry, something went wrong with this version!\n"
            f"Version: {__VERSION__}\n"
            f"Error: {err}\n"
            f"Config: {config['settings']}"
        )
        raise err
