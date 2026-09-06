"""Loads the guardrails policy: a per-entity action, plus any custom regex
recognizers an entity carries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ACTIONS = {"block", "redact", "allow"}
DEFAULT_SCORE_THRESHOLD = 0.4

DEFAULT_POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "policy.yaml"


@dataclass
class PatternSpec:
    name: str
    regex: str
    score: float = 0.85
    # Nearby words (e.g. "cedula") that boost this pattern's score when
    # present — lets a pattern otherwise too ambiguous to trust on its own
    # (bare digits) only fire in the right context.
    context: list[str] = field(default_factory=list)


@dataclass
class EntityRule:
    action: str
    patterns: list[PatternSpec] = field(default_factory=list)


@dataclass
class Policy:
    entities: dict[str, EntityRule]
    score_threshold: float = DEFAULT_SCORE_THRESHOLD

    def action_for(self, entity_type: str) -> str:
        rule = self.entities.get(entity_type)
        return rule.action if rule else "allow"

    @property
    def custom_entities(self) -> dict[str, EntityRule]:
        return {name: rule for name, rule in self.entities.items() if rule.patterns}


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> Policy:
    raw = yaml.safe_load(path.read_text())
    entities = {}
    for name, cfg in raw["entities"].items():
        if cfg["action"] not in ACTIONS:
            raise ValueError(f"invalid action {cfg['action']!r} for entity {name}")
        patterns = [
            PatternSpec(
                name=p["name"],
                regex=p["regex"],
                score=p.get("score", 0.85),
                context=p.get("context", []),
            )
            for p in cfg.get("patterns", [])
        ]
        entities[name] = EntityRule(action=cfg["action"], patterns=patterns)
    return Policy(
        entities=entities,
        score_threshold=raw.get("score_threshold", DEFAULT_SCORE_THRESHOLD),
    )
