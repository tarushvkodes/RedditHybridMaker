import os
import re
import subprocess
import sys
import time
from typing import List

import spacy

from utils.console import print_step
from utils.voice import sanitize_text


def _fallback_sentence_split(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if c and sanitize_text(c)]


# working good

def posttextparser(obj, *, tried: bool = False) -> List[str]:
    text: str = re.sub("\n", " ", obj or "")
    if not text.strip():
        return []

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError as e:
        if not tried:
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                time.sleep(2)
                return posttextparser(obj, tried=True)
            except Exception:
                pass

        print_step(
            "spaCy model unavailable. Falling back to regex sentence splitting (install with: python -m spacy download en_core_web_sm)."
        )
        return _fallback_sentence_split(text)

    doc = nlp(text)
    newtext: List[str] = []

    for line in doc.sents:
        if sanitize_text(line.text):
            newtext.append(line.text)

    return newtext if newtext else _fallback_sentence_split(text)
