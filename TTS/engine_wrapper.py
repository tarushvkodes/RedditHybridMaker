import os
import re
import subprocess
from pathlib import Path
from typing import Tuple

import numpy as np
import translators
from moviepy.audio.AudioClip import AudioClip
from moviepy.audio.fx.volumex import volumex
from moviepy.editor import AudioFileClip
from rich.progress import track

from utils import settings
from utils.console import print_step, print_substep
from utils.voice import sanitize_text

DEFAULT_MAX_LENGTH: int = (
    50  # Video length variable, edit this on your own risk. It should work, but it's not supported
)

DEFAULT_PROFANITY_WORDS = {
    "fuck",
    "fucking",
    "fucked",
    "shit",
    "shitty",
    "bitch",
    "bastard",
    "asshole",
    "motherfucker",
    "dick",
    "pussy",
    "cunt",
    "slut",
    "whore",
}


class TTSEngine:
    """Calls the given TTS engine to reduce code duplication and allow multiple TTS engines.

    Args:
        tts_module            : The TTS module. Your module should handle the TTS itself and saving to the given path under the run method.
        reddit_object         : The reddit object that contains the posts to read.
        path (Optional)       : The unix style path to save the mp3 files to. This must not have leading or trailing slashes.
        max_length (Optional) : The maximum length of the mp3 files in total.

    Notes:
        tts_module must take the arguments text and filepath.
    """

    def __init__(
        self,
        tts_module,
        reddit_object: dict,
        path: str = "assets/temp/",
        max_length: int = DEFAULT_MAX_LENGTH,
        last_clip_length: int = 0,
    ):
        self.tts_module = tts_module()
        self.reddit_object = reddit_object

        self.redditid = re.sub(r"[^\w\s-]", "", reddit_object["thread_id"])
        self.path = path + self.redditid + "/mp3"
        self.max_length = max_length
        self.length = 0
        self.last_clip_length = last_clip_length

    def add_periods(
        self,
    ):  # adds periods to the end of paragraphs (where people often forget to put them) so tts doesn't blend sentences
        for comment in self.reddit_object["comments"]:
            # remove links
            regex_urls = r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
            comment["comment_body"] = re.sub(regex_urls, " ", comment["comment_body"])
            comment["comment_body"] = comment["comment_body"].replace("\n", ". ")
            comment["comment_body"] = re.sub(r"\bAI\b", "A.I", comment["comment_body"])
            comment["comment_body"] = re.sub(r"\bAGI\b", "A.G.I", comment["comment_body"])
            if comment["comment_body"][-1] != ".":
                comment["comment_body"] += "."
            comment["comment_body"] = comment["comment_body"].replace(". . .", ".")
            comment["comment_body"] = comment["comment_body"].replace(".. . ", ".")
            comment["comment_body"] = comment["comment_body"].replace(". . ", ".")
            comment["comment_body"] = re.sub(r'\."\.', '".', comment["comment_body"])

    def run(self) -> Tuple[int, int]:
        Path(self.path).mkdir(parents=True, exist_ok=True)
        print_step("Saving Text to MP3 files...")

        self.add_periods()
        self.call_tts("title", process_text(self.reddit_object["thread_title"]))
        # processed_text = ##self.reddit_object["thread_post"] != ""
        idx = 0

        # Handle hybrid mode - process both post content and comments
        if settings.config["settings"].get("hybrid_mode", False):
            # First process the post content
            if settings.config["settings"]["storymodemethod"] == 0:
                if len(self.reddit_object["thread_post"]) > self.tts_module.max_chars:
                    self.split_post(self.reddit_object["thread_post"], "postaudio")
                else:
                    self.call_tts("postaudio", process_text(self.reddit_object["thread_post"]))
            elif settings.config["settings"]["storymodemethod"] == 1:
                for idx, text in track(enumerate(self.reddit_object["thread_post"])):
                    self.call_tts(f"postaudio-{idx}", process_text(text))
            
            # Then process the comments
            comment_start_idx = idx + 1 if settings.config["settings"]["storymodemethod"] == 1 else 1
            for comment_idx, comment in track(enumerate(self.reddit_object["comments"][: settings.config["settings"].get("hybrid_comments_count", 1)], start=comment_start_idx), "Processing comments..."):
                # Stop creating mp3 files if the length is greater than max length
                if self.length > self.max_length and comment_idx > comment_start_idx:
                    self.length -= self.last_clip_length
                    comment_idx -= 1
                    break
                if (
                    len(comment["comment_body"]) > self.tts_module.max_chars
                ):  # Split the comment if it is too long
                    self.split_post(comment["comment_body"], f"comment-{comment_idx}")
                else:  # If the comment is not too long, just call the tts engine
                    self.call_tts(f"comment-{comment_idx}", process_text(comment["comment_body"]))
            
            idx = comment_start_idx + len(self.reddit_object["comments"]) - 1
            
        elif settings.config["settings"]["storymode"]:
            if settings.config["settings"]["storymodemethod"] == 0:
                if len(self.reddit_object["thread_post"]) > self.tts_module.max_chars:
                    self.split_post(self.reddit_object["thread_post"], "postaudio")
                else:
                    self.call_tts("postaudio", process_text(self.reddit_object["thread_post"]))
            elif settings.config["settings"]["storymodemethod"] == 1:
                for idx, text in track(enumerate(self.reddit_object["thread_post"])):
                    self.call_tts(f"postaudio-{idx}", process_text(text))

        else:
            for idx, comment in track(enumerate(self.reddit_object["comments"]), "Saving..."):
                # ! Stop creating mp3 files if the length is greater than max length.
                if self.length > self.max_length and idx > 1:
                    self.length -= self.last_clip_length
                    idx -= 1
                    break
                if (
                    len(comment["comment_body"]) > self.tts_module.max_chars
                ):  # Split the comment if it is too long
                    self.split_post(comment["comment_body"], idx)  # Split the comment
                else:  # If the comment is not too long, just call the tts engine
                    self.call_tts(f"{idx}", process_text(comment["comment_body"]))

        print_substep("Saved Text to MP3 files successfully.", style="bold green")
        return self.length, idx

    def split_post(self, text: str, idx):
        split_files = []
        split_text = [
            x.group().strip()
            for x in re.finditer(
                r" *(((.|\n){0," + str(self.tts_module.max_chars) + "})(\.|.$))", text
            )
        ]
        self.create_silence_mp3()

        idy = None
        for idy, text_cut in enumerate(split_text):
            newtext = process_text(text_cut)
            # print(f"{idx}-{idy}: {newtext}\n")

            if not newtext or newtext.isspace():
                print("newtext was blank because sanitized split text resulted in none")
                continue
            else:
                self.call_tts(f"{idx}-{idy}.part", newtext)
                with open(f"{self.path}/list.txt", "w") as f:
                    for idz in range(0, len(split_text)):
                        f.write("file " + f"'{idx}-{idz}.part.mp3'" + "\n")
                    split_files.append(str(f"{self.path}/{idx}-{idy}.part.mp3"))
                    f.write("file " + f"'silence.mp3'" + "\n")

                os.system(
                    "ffmpeg -f concat -y -hide_banner -loglevel panic -safe 0 "
                    + "-i "
                    + f"{self.path}/list.txt "
                    + "-c copy "
                    + f"{self.path}/{idx}.mp3"
                )
        try:
            for i in range(0, len(split_files)):
                os.unlink(split_files[i])
        except FileNotFoundError as e:
            print("File not found: " + e.filename)
        except OSError:
            print("OSError")

    def _build_profanity_set(self):
        tts_cfg = settings.config["settings"]["tts"]
        custom = tts_cfg.get("censored_words", "")
        custom_words = {
            w.strip().lower()
            for w in str(custom).split(",")
            if w and w.strip()
        }
        return DEFAULT_PROFANITY_WORDS.union(custom_words)

    def _is_profanity_token(self, token: str, profanity_words) -> bool:
        cleaned = re.sub(r"[^a-zA-Z0-9']", "", token).lower()
        if not cleaned:
            return False
        if cleaned in profanity_words:
            return True
        for word in profanity_words:
            if cleaned.startswith(word) and len(cleaned) <= len(word) + 3:
                return True
        return False

    def _make_silence_file(self, filepath: str, duration: float):
        safe_duration = max(0.12, float(duration))
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                f"{safe_duration:.3f}",
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                filepath,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _call_tts_with_profanity_silence(self, filename: str, text: str):
        tts_cfg = settings.config["settings"]["tts"]
        profanity_words = self._build_profanity_set()
        base_word_silence = float(tts_cfg.get("censor_word_silence_sec", 0.35))
        per_char_silence = float(tts_cfg.get("censor_char_silence_sec", 0.02))

        tokens = re.split(r"(\s+)", text)
        parts = []
        current_speech = []

        for token in tokens:
            if token == "":
                continue
            if self._is_profanity_token(token, profanity_words):
                if current_speech:
                    parts.append(("speech", "".join(current_speech)))
                    current_speech = []
                cleaned = re.sub(r"[^a-zA-Z0-9']", "", token)
                duration = base_word_silence + len(cleaned) * per_char_silence
                parts.append(("silence", duration))
            else:
                current_speech.append(token)

        if current_speech:
            parts.append(("speech", "".join(current_speech)))

        if not parts:
            self.tts_module.run(
                text,
                filepath=f"{self.path}/{filename}.mp3",
                random_voice=tts_cfg["random_voice"],
            )
            return

        part_files = []
        part_idx = 0
        for kind, payload in parts:
            part_path = f"{self.path}/{filename}.part{part_idx}.mp3"
            if kind == "speech":
                speech_text = str(payload).strip()
                if not speech_text:
                    continue
                self.tts_module.run(
                    speech_text,
                    filepath=part_path,
                    random_voice=tts_cfg["random_voice"],
                )
            else:
                self._make_silence_file(part_path, float(payload))
            part_files.append(part_path)
            part_idx += 1

        if not part_files:
            self._make_silence_file(f"{self.path}/{filename}.mp3", base_word_silence)
            return

        list_file = f"{self.path}/{filename}.parts.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in part_files:
                escaped = p.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_file,
                "-c:a",
                "libmp3lame",
                "-q:a",
                "4",
                f"{self.path}/{filename}.mp3",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for p in part_files:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.remove(list_file)
        except OSError:
            pass

    def call_tts(self, filename: str, text: str):
        tts_cfg = settings.config["settings"]["tts"]
        censor_enabled = bool(tts_cfg.get("censor_swear_words", False))

        if censor_enabled:
            self._call_tts_with_profanity_silence(filename, text)
        else:
            self.tts_module.run(
                text,
                filepath=f"{self.path}/{filename}.mp3",
                random_voice=tts_cfg["random_voice"],
            )

        try:
            clip = AudioFileClip(f"{self.path}/{filename}.mp3")
            self.last_clip_length = clip.duration
            self.length += clip.duration
            clip.close()
        except:
            self.length = 0

    def create_silence_mp3(self):
        silence_duration = settings.config["settings"]["tts"]["silence_duration"]
        silence = AudioClip(
            make_frame=lambda t: np.sin(440 * 2 * np.pi * t),
            duration=silence_duration,
            fps=44100,
        )
        silence = volumex(silence, 0)
        silence.write_audiofile(f"{self.path}/silence.mp3", fps=44100, verbose=False, logger=None)


def process_text(text: str, clean: bool = True):
    lang = settings.config["reddit"]["thread"]["post_lang"]
    new_text = sanitize_text(text) if clean else text
    if lang:
        print_substep("Translating Text...")
        translated_text = translators.translate_text(text, translator="google", to_language=lang)
        new_text = sanitize_text(translated_text)
    return new_text
