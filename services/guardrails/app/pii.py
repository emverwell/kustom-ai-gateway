"""PII detection and enforcement: Presidio's built-in recognizers plus any
custom ones from the policy, gated by each entity's configured action."""

from __future__ import annotations

from dataclasses import dataclass, field

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .policy import Policy


@dataclass
class PiiVerdict:
    decision: str  # "block" or "allow"
    text: str  # original text, or with "redact" entities replaced
    entities_found: list[str] = field(default_factory=list)


class PiiEngine:
    def __init__(self, policy: Policy):
        self._policy = policy
        self._analyzer = AnalyzerEngine()
        for name, rule in policy.custom_entities.items():
            # One recognizer per pattern (not one recognizer for all of an
            # entity's patterns) because Presidio's `context` boost applies
            # per-recognizer — a pattern needing context (e.g. bare digits)
            # and one that doesn't (e.g. a clearly-prefixed ID) can't share one.
            for spec in rule.patterns:
                recognizer = PatternRecognizer(
                    supported_entity=name,
                    patterns=[Pattern(name=spec.name, regex=spec.regex, score=spec.score)],
                    context=spec.context or None,
                )
                self._analyzer.registry.add_recognizer(recognizer)
        self._anonymizer = AnonymizerEngine()

    def evaluate(self, text: str) -> PiiVerdict:
        results = self._analyzer.analyze(
            text=text,
            entities=list(self._policy.entities),
            language="en",
            score_threshold=self._policy.score_threshold,
        )
        entities_found = sorted({r.entity_type for r in results})

        if any(self._policy.action_for(r.entity_type) == "block" for r in results):
            return PiiVerdict(decision="block", text=text, entities_found=entities_found)

        to_redact = [r for r in results if self._policy.action_for(r.entity_type) == "redact"]
        if not to_redact:
            return PiiVerdict(decision="allow", text=text, entities_found=entities_found)

        operators = {
            r.entity_type: OperatorConfig("replace", {"new_value": f"<{r.entity_type}>"})
            for r in to_redact
        }
        redacted = self._anonymizer.anonymize(
            text=text, analyzer_results=to_redact, operators=operators
        )
        return PiiVerdict(decision="allow", text=redacted.text, entities_found=entities_found)
