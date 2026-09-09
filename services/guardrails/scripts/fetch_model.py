"""Fetch the pinned ONNX prompt-injection model + tokenizer from the
ProtectAI HF repo, at an exact commit SHA (not a moving branch ref).

Run at Docker build time (step 6) and locally for standalone testing (5b).
No conversion happens here — the repo already ships an ONNX export.
"""

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "protectai/deberta-v3-base-prompt-injection-v2"
REVISION = "90c9989b1a342275dd0d1a95aad283c04e075671"
FILES = [
    "onnx/model.onnx",
    "onnx/config.json",
    "onnx/tokenizer.json",
    "onnx/tokenizer_config.json",
    "onnx/special_tokens_map.json",
    "onnx/spm.model",
    "onnx/added_tokens.json",
]
DEST = Path(__file__).resolve().parent.parent / ".models" / "prompt-injection"
MAX_ATTEMPTS = 4


def fetch_with_retries(url: str, dest: Path) -> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            urllib.request.urlretrieve(url, dest)
            return
        except (urllib.error.URLError, urllib.error.ContentTooShortError, OSError) as e:
            dest.unlink(missing_ok=True)  # don't leave a truncated file behind
            if attempt == MAX_ATTEMPTS:
                raise
            wait = 2**attempt
            print(f"  attempt {attempt} failed ({e}); retrying in {wait}s")
            time.sleep(wait)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{f}"
        dest = DEST / Path(f).name
        print(f"fetching {url} -> {dest}")
        fetch_with_retries(url, dest)


if __name__ == "__main__":
    sys.exit(main())
