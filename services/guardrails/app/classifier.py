"""Prompt-injection classification behind a swappable backend interface.

Two implementations: `onnx` (default, actually implemented) and `ollama`
(a stub — demonstrates the abstraction without pulling in an Ollama client
dependency).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / ".models" / "prompt-injection"
LABELS = ["SAFE", "INJECTION"]


@dataclass
class ClassifierVerdict:
    label: str  # "SAFE" or "INJECTION"
    score: float  # confidence in `label`


class InjectionClassifier(ABC):
    @abstractmethod
    def classify(self, text: str) -> ClassifierVerdict: ...


class OnnxInjectionClassifier(InjectionClassifier):
    """Runs the pinned ProtectAI deberta-v3 ONNX export fetched by
    scripts/fetch_model.py. Model expects only input_ids + attention_mask
    (verified against the actual exported graph — no token_type_ids)."""

    def __init__(self, model_dir: Path = DEFAULT_MODEL_DIR):
        self._tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self._session = ort.InferenceSession(
            str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"]
        )

    def classify(self, text: str) -> ClassifierVerdict:
        encoding = self._tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
        (logits,) = self._session.run(
            None, {"input_ids": input_ids, "attention_mask": attention_mask}
        )
        exp = np.exp(logits[0])
        probs = exp / exp.sum()
        idx = int(np.argmax(probs))
        return ClassifierVerdict(label=LABELS[idx], score=float(probs[idx]))


class OllamaInjectionClassifier(InjectionClassifier):
    """Stub: shows the shape a second backend would take without adding an
    Ollama client dependency. Not wired up as a selectable option — `onnx`
    is the only implemented backend."""

    def classify(self, text: str) -> ClassifierVerdict:
        raise NotImplementedError(
            "ollama backend is a stub; onnx is the only implemented backend"
        )


def get_classifier(backend: str = "onnx") -> InjectionClassifier:
    if backend == "onnx":
        return OnnxInjectionClassifier()
    if backend == "ollama":
        return OllamaInjectionClassifier()
    raise ValueError(f"unknown classifier backend: {backend!r}")
