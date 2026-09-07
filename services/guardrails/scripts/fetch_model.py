"""Fetch the pinned ONNX prompt-injection model + tokenizer from the
ProtectAI HF repo, at an exact commit SHA (not a moving branch ref).

Run at Docker build time (step 6) and locally for standalone testing (5b).
No conversion happens here — the repo already ships an ONNX export.
"""

import sys
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


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{f}"
        dest = DEST / Path(f).name
        print(f"fetching {url} -> {dest}")
        urllib.request.urlretrieve(url, dest)


if __name__ == "__main__":
    sys.exit(main())
